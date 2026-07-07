#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 3 最小可用脚手架：Web 上传 → 后台转换 → 在线阅读 / 下载 zip

设计目标
--------
- 纯标准库（http.server / urllib / subprocess / zipfile），零第三方依赖，clone 即可跑。
- 上传 PDF → 调 converter/convert.py 生成 converted/<名>/ → 返回在线阅读链接 + 下载 zip。
- 转换器复用项目已有的 CLI，不重复造轮子。

运行
----
    python server/web_app.py                 # 默认 http://127.0.0.1:8000
    PORT=9000 python server/web_app.py       # 自定义端口

注意
----
- 这是「远景计划」的脚手架版：单进程、同步转换、无鉴权、无并发队列。
  生产化需加：异步任务队列、上传大小限制、鉴权、清理策略（见文件末尾 TODO）。
- OCR 文字版需系统已装 tesseract；否则扫描版退化为纯图片（转换器自动处理）。
"""

import os
import sys
import json
import shutil
import subprocess
import zipfile
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO_ROOT = Path(__file__).resolve().parent.parent
CONVERT = REPO_ROOT / 'converter' / 'convert.py'
UPLOAD_DIR = REPO_ROOT / 'uploads'
CONVERTED_DIR = REPO_ROOT / 'converted'
PORT = int(os.environ.get('PORT', '8000'))


def ensure_dirs():
    UPLOAD_DIR.mkdir(exist_ok=True)
    CONVERTED_DIR.mkdir(exist_ok=True)


def run_convert(pdf_path: Path, out_name: str, dpi: int = 110, ocr: bool = False):
    """调用转换器，返回 (success, out_dir, log)。"""
    out_dir = CONVERTED_DIR / out_name
    cmd = [sys.executable, str(CONVERT), str(pdf_path),
           '-o', str(out_dir), '--title', out_name, '--dpi', str(dpi)]
    if ocr:
        cmd.append('--ocr')
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    ok = proc.returncode == 0 and (out_dir / 'index.html').exists()
    return ok, out_dir, proc.stdout + proc.stderr


def zip_folder(folder: Path, zip_path: Path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in folder.rglob('*'):
            if f.is_file():
                z.write(f, f.relative_to(folder))


HTML_PAGE = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>算法书 · 上传转 HTML</title>
<style>
body{{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;max-width:640px;margin:40px auto;padding:0 16px;color:#2b2b2b;line-height:1.7}}
h1{{font-size:22px}} .card{{border:1px solid #e5e5e8;border-radius:10px;padding:20px;background:#fafafa}}
input[type=file]{{margin:12px 0}} button{{background:#4b6bff;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:14px}}
.note{{font-size:12px;color:#777;margin-top:8px}} a{{color:#2540b8}}
</style></head>
<body>
<h1>📚 算法书 · PDF → 自包含 HTML</h1>
<div class="card">
  <form method="post" enctype="multipart/form-data">
    <div>选择一本 PDF：</div>
    <input type="file" name="pdf" accept="application/pdf" required>
    <div><label><input type="checkbox" name="ocr"> 开启 OCR（需服务器已装 tesseract）</label></div>
    <button type="submit">上传并转换</button>
  </form>
  <div class="note">转换在服务器后台进行，扫描版全本可能需数十秒～几分钟。</div>
</div>
{result}
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body: bytes, ctype='text/html; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith('/read/'):
            # 在线阅读：直接伺服 converted/<名>/index.html
            name = urllib.parse.unquote(self.path[len('/read/'):])
            target = (CONVERTED_DIR / name / 'index.html')
            if target.exists():
                self._send(200, target.read_bytes(), 'text/html; charset=utf-8')
            else:
                self._send(404, b'not found')
            return
        if self.path.startswith('/download/'):
            name = urllib.parse.unquote(self.path[len('/download/'):]).rstrip('/')
            name = name[:-4] if name.endswith('.zip') else name
            zp = UPLOAD_DIR / (name + '.zip')
            if zp.exists():
                self._send(200, zp.read_bytes(), 'application/zip')
            else:
                self._send(404, b'not found')
            return
        self._send(200, HTML_PAGE.format(result='').encode('utf-8'))

    def do_POST(self):
        ctype = self.headers.get('Content-Type', '')
        if 'multipart/form-data' not in ctype:
            self._send(400, b'expected multipart/form-data')
            return
        length = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(length)
        boundary = ctype.split('boundary=')[1].encode()
        parts = raw.split(b'--' + boundary)
        pdf_bytes = None
        ocr = False
        for p in parts:
            if b'filename="' in p and b'application/pdf' in p:
                hd, _, body = p.partition(b'\r\n\r\n')
                pdf_bytes = body[:-2] if body.endswith(b'\r\n') else body
                fn = hd.split(b'filename="')[1].split(b'"')[0].decode('utf-8', 'ignore')
                self._pdf_name = Path(fn).stem
            elif b'name="ocr"' in p:
                ocr = True
        if not pdf_bytes:
            self._send(400, b'no pdf')
            return
        name = self._pdf_name or 'upload'
        pdf_path = UPLOAD_DIR / (name + '.pdf')
        pdf_path.write_bytes(pdf_bytes)
        ok, out_dir, log = run_convert(pdf_path, name, ocr=ocr)
        if not ok:
            result = f'<div class="card" style="margin-top:16px;color:#b00"><b>转换失败</b><pre>{log[-2000:]}</pre></div>'
            self._send(200, HTML_PAGE.format(result=result).encode('utf-8'))
            return
        # 打包 zip
        zp = UPLOAD_DIR / (name + '.zip')
        zip_folder(out_dir, zp)
        result = (f'<div class="card" style="margin-top:16px">'
                  f'<b>✅ 转换完成：</b>{name}<br>'
                  f'📖 <a href="/read/{urllib.parse.quote(name)}/" target="_blank">在线阅读</a> &nbsp; '
                  f'⬇️ <a href="/download/{urllib.parse.quote(name)}.zip">下载 zip</a>'
                  f'</div>')
        self._send(200, HTML_PAGE.format(result=result).encode('utf-8'))

    def log_message(self, *args):
        pass  # 静默


def main():
    ensure_dirs()
    if not CONVERT.exists():
        sys.stderr.write(f'找不到转换器: {CONVERT}\n')
        sys.exit(1)
    srv = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'算法书 Web 转换服务已启动: http://127.0.0.1:{PORT}')
    print(f'  转换器: {CONVERT}')
    print(f'  输出目录: {CONVERTED_DIR}')
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == '__main__':
    main()

# ---------------------------------------------------------------------------
# TODO（生产化方向，非本脚手架范围）：
#  - 异步任务队列（转换阻塞请求线程）→ Celery / 子进程池 + 轮询/WebSocket
#  - 上传大小 / 类型 / 频率限制，防滥用
#  - 鉴权（token / 登录），避免公开被当成免费转换服务
#  - 定时清理 uploads/ 与过期 converted/
#  - OCR 需服务器预装 tesseract + chi_sim，否则自动降级纯图片
# ---------------------------------------------------------------------------
