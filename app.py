#!/usr/bin/env python3
"""
app.py - 文字型 PDF → 可批注 HTML 网页（后端）

* 纯标准库 HTTP 服务（http.server），不依赖 Flask 等框架
* PDF 文本/版式抽取用 PyMuPDF（pip install -r requirements.txt）
* 上传的 PDF 抽取成紧凑 JSON 后即刻丢弃源文件，不占空间
* 批注以 JSON 存于 data/<id>/annotations.json，刷新不丢

运行：
    pip install -r requirements.txt
    python app.py                 # 默认 http://127.0.0.1:8000
    python app.py --port 9000 --host 0.0.0.0
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

import pdftext

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(ROOT, "static")
DATA_DIR = os.path.join(ROOT, "data")

ID_RE = re.compile(r"^[\w-]+$")


# ----------------------------- 存储辅助 -----------------------------

def doc_dir(doc_id: str) -> str:
    return os.path.join(DATA_DIR, doc_id)


def doc_json_path(doc_id: str) -> str:
    return os.path.join(doc_dir(doc_id), "doc.json")


def ann_path(doc_id: str) -> str:
    return os.path.join(doc_dir(doc_id), "annotations.json")


def index_path() -> str:
    return os.path.join(DATA_DIR, "index.json")


def list_docs():
    p = index_path()
    if not os.path.exists(p):
        return []
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return []


def add_to_index(doc_id: str, filename: str, title: str, page_count: int):
    docs = list_docs()
    docs.insert(0, {
        "id": doc_id,
        "filename": filename,
        "title": title,
        "page_count": page_count,
        "created": int(time.time()),
    })
    with open(index_path(), "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)


def save_annotations(doc_id: str, data):
    if not isinstance(data, list):
        raise ValueError("annotations must be a list")
    with open(ann_path(doc_id), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------------- 导出独立 HTML -----------------------------

EXPORT_TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · 批注版</title>
<style>{css}</style>
</head>
<body class="standalone">
<div id="viewer" class="view">
  <div id="toolbar">
    <button id="btn-back" class="tb-btn" title="返回">←</button>
    <span class="tb-title" id="doc-title">{title}</span>
    <span class="spacer"></span>
    <label class="tb-zoom">缩放
      <input id="zoom" type="range" min="0.5" max="3" step="0.1" value="1.2">
      <span id="zoom-val">1.2x</span>
    </label>
    <span class="hint">选中正文文字即可高亮 / 下划线 / 批注 · 本文件为独立副本，批注存于本机浏览器</span>
  </div>
  <div id="main">
    <div id="pages"></div>
    <aside id="sidebar">
      <div class="sb-head">我的批注 <span id="ann-count">0</span></div>
      <div id="ann-list"></div>
      <p class="muted sb-tip">选中正文文字 → 点「高亮 / 下划线 / 批注」即可标注；点右侧卡片可跳转。</p>
    </aside>
  </div>
</div>

<div id="sel-bar" class="sel-bar hidden">
  <button data-act="highlight">高亮</button>
  <button data-act="underline">下划线</button>
  <button data-act="note">批注</button>
  <button data-act="cancel">取消</button>
</div>

<script>window.__EMBEDDED__ = {payload};</script>
<script>{js}</script>
</body>
</html>"""


def build_export(doc_id: str):
    d = doc_dir(doc_id)
    if not os.path.exists(doc_json_path(doc_id)):
        return None
    with open(doc_json_path(doc_id), encoding="utf-8") as f:
        doc = json.load(f)
    ann = []
    if os.path.exists(ann_path(doc_id)):
        with open(ann_path(doc_id), encoding="utf-8") as f:
            ann = json.load(f)
    css = open(os.path.join(STATIC_DIR, "style.css"), encoding="utf-8").read()
    js = open(os.path.join(STATIC_DIR, "app.js"), encoding="utf-8").read()
    payload = json.dumps({"doc": doc, "annotations": ann}, ensure_ascii=False)
    title = (doc.get("title") or doc.get("filename") or "document").replace('"', "")
    return EXPORT_TEMPLATE.format(css=css, js=js, payload=payload, title=title)


# ----------------------------- HTTP 处理 -----------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "PDFAnnotate/1.0"
    protocol_version = "HTTP/1.1"

    # 让日志安静一点
    def log_message(self, *args):
        pass

    def _send(self, body: bytes, content_type: str, extra=None):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: str, content_type: str):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except FileNotFoundError:
            self.send_error(404)
            return
        self._send(data, content_type)

    def _ctype(self, name: str) -> str:
        if name.endswith(".html"):
            return "text/html; charset=utf-8"
        if name.endswith(".css"):
            return "text/css; charset=utf-8"
        if name.endswith(".js"):
            return "application/javascript; charset=utf-8"
        if name.endswith(".png"):
            return "image/png"
        if name.endswith((".jpg", ".jpeg")):
            return "image/jpeg"
        if name.endswith(".svg"):
            return "image/svg+xml"
        return "application/octet-stream"

    # ---------------- GET ----------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            return self._send_file(os.path.join(STATIC_DIR, "index.html"),
                                   "text/html; charset=utf-8")
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            full = os.path.normpath(os.path.join(STATIC_DIR, rel))
            if not full.startswith(STATIC_DIR):
                return self.send_error(403)
            return self._send_file(full, self._ctype(rel))

        if path.startswith("/api/"):
            return self._api_get(path)

        self.send_error(404)

    def _api_get(self, path: str):
        if path == "/api/info":
            return self._send_json({"tool": "pdf-annotate", "version": "1.0"})

        if path == "/api/docs":
            return self._send_json(list_docs())

        m = re.match(r"^/api/doc/([\w-]+)$", path)
        if m:
            return self._send_file(doc_json_path(m.group(1)),
                                   "application/json; charset=utf-8")

        m = re.match(r"^/api/annotations/([\w-]+)$", path)
        if m:
            p = ann_path(m.group(1))
            if not os.path.exists(p):
                return self._send_json([])
            return self._send_file(p, "application/json; charset=utf-8")

        m = re.match(r"^/api/doc/([\w-]+)/img/([\w.-]+)$", path)
        if m:
            full = os.path.join(doc_dir(m.group(1)), "img", m.group(2))
            return self._send_file(full, "image/png" if full.endswith(".png") else "image/jpeg")

        m = re.match(r"^/api/doc/([\w-]+)/pageimg/(\d+)\.png$", path)
        if m:
            full = os.path.join(doc_dir(m.group(1)), "pageimg", m.group(2) + ".png")
            return self._send_file(full, "image/png")

        m = re.match(r"^/api/export/([\w-]+)$", path)
        if m:
            html = build_export(m.group(1))
            if html is None:
                return self.send_error(404)
            self._send(
                html.encode("utf-8"),
                "text/html; charset=utf-8",
                extra={"Content-Disposition": f'attachment; filename="{m.group(1)}-annotated.html"'},
            )
            return

        self.send_error(404)

    # ---------------- POST ----------------
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/upload":
            return self._upload()

        m = re.match(r"^/api/annotations/([\w-]+)$", path)
        if m:
            doc_id = m.group(1)
            length = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
            except Exception:
                return self._send_json({"error": "invalid json"}, 400)
            try:
                save_annotations(doc_id, data)
            except Exception as e:
                return self._send_json({"error": str(e)}, 400)
            return self._send_json({"ok": True})

        self.send_error(404)

    # ---------------- DELETE ----------------
    def do_DELETE(self):
        m = re.match(r"^/api/doc/([\w-]+)$", self.path)
        if m:
            doc_id = m.group(1)
            d = doc_dir(doc_id)
            if os.path.isdir(d):
                shutil.rmtree(d, ignore_errors=True)
                docs = [x for x in list_docs() if x["id"] != doc_id]
                with open(index_path(), "w", encoding="utf-8") as f:
                    json.dump(docs, f, ensure_ascii=False, indent=2)
                return self._send_json({"ok": True})
            return self.send_error(404)
        self.send_error(404)

    # ---------------- 上传 ----------------
    def _upload(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length <= 0:
            return self._send_json({"error": "empty body"}, 400)
        raw = self.rfile.read(length)
        if raw[:4] != b"%PDF":
            return self._send_json({"error": "不是 PDF 文件"}, 400)

        filename = unquote(self.headers.get("X-Filename", "document.pdf"))
        # 安全文件名
        safe = re.sub(r"[^\w.\-一-鿿]", "_", filename) or "document.pdf"

        tmp = os.path.join(DATA_DIR, "_tmp_" + uuid.uuid4().hex + ".pdf")
        with open(tmp, "wb") as f:
            f.write(raw)

        doc_id = uuid.uuid4().hex[:12]
        d = doc_dir(doc_id)
        os.makedirs(os.path.join(d, "img"), exist_ok=True)
        os.makedirs(os.path.join(d, "pageimg"), exist_ok=True)

        try:
            meta, pages = pdftext.extract(tmp)
        except Exception as e:
            shutil.rmtree(d, ignore_errors=True)
            try:
                os.remove(tmp)
            except OSError:
                pass
            return self._send_json({"error": f"抽取失败：{e}"}, 500)

        # 落盘图片 + 图页兜底 + 给图片补 src
        for pno, page in enumerate(pages):
            for im in page["imgs"]:
                try:
                    data, ext = pdftext.extract_image(tmp, im["xref"])
                    fname = f"{im['xref']}.{ext}"
                    with open(os.path.join(d, "img", fname), "wb") as f:
                        f.write(data)
                    im["src"] = f"/api/doc/{doc_id}/img/{fname}"
                except Exception:
                    im.pop("src", None)
            if page["text_len"] < 15:
                try:
                    data = pdftext.render_page_image(tmp, pno, dpi=100)
                    with open(os.path.join(d, "pageimg", f"{pno}.png"), "wb") as f:
                        f.write(data)
                    page["image_page"] = f"/api/doc/{doc_id}/pageimg/{pno}.png"
                except Exception:
                    pass
            page.pop("text_len", None)

        title = meta["title"] or safe
        record = {
            "id": doc_id,
            "filename": safe,
            "title": title,
            "author": meta["author"],
            "page_count": meta["page_count"],
            "pages": pages,
        }
        with open(doc_json_path(doc_id), "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        with open(ann_path(doc_id), "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)

        add_to_index(doc_id, safe, title, meta["page_count"])

        # 抽取完成即丢弃源 PDF，不占空间（符合「不膨胀磁盘」理念）
        try:
            os.remove(tmp)
        except OSError:
            pass

        self._send_json({
            "id": doc_id,
            "title": title,
            "page_count": meta["page_count"],
            "filename": safe,
        })


def main():
    global DATA_DIR
    ap = argparse.ArgumentParser(description="文字型 PDF → 可批注 HTML 网页")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--data-dir", default=DATA_DIR)
    args = ap.parse_args()

    DATA_DIR = os.path.abspath(args.data_dir)
    os.makedirs(DATA_DIR, exist_ok=True)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    print("PDF 批注工坊已启动 →", url)
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
