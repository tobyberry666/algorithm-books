"""
pdftext.py - 从「文字型 PDF」抽取文字 + 版式 + 图片，得到紧凑 JSON。

设计目标（与「逐页栅格化成上百张 PNG」相反）：
  * 每一页只记录文字 span 的绝对坐标 / 字号 / 颜色 / 字重 / 字体；
  * 内嵌图片按其包围盒定位（仅图，不整页栅格化）；
  * 对「几乎全是图」的页面（扫描页 / 大图页）才退化为单张 PNG 兜底。
这样一本几百页的书，本地产物通常只有 2 个 JSON + 少量图片，
而不是成百上千张栅格图 —— 既省空间又让文字可选中、可批注。
"""

from __future__ import annotations

import fitz  # PyMuPDF


def _css_color(color_int: int) -> str:
    """PyMuPDF 文字颜色是 0xRRGGBB 整数，转成 #rrggbb。"""
    return f"#{int(color_int) & 0xFFFFFF:06x}"


def _style_from_font(flags: int, font: str):
    fl = (font or "").lower()
    weight = "bold" if (flags & 16) or ("bold" in fl) else "normal"
    style = "italic" if (flags & 2) or ("italic" in fl) else "normal"
    return weight, style


def extract(pdf_path: str):
    """返回 (meta, pages)。

    meta = {"title", "author", "page_count"}
    pages[i] = {
        "w", "h",                 # 页面尺寸（点，1pt = 1/72 inch）
        "spans": [ {t,x,y,w,h,size,font,color,weight,style}, ... ],
        "imgs":  [ {xref,x,y,w,h}, ... ],   # 内嵌图片包围盒（src 由后端补全）
        "text_len": int,          # 该页纯文字长度，用于判定是否「图页」
    }
    """
    doc = fitz.open(pdf_path)
    pages = []
    for pno in range(doc.page_count):
        page = doc[pno]
        pw = round(page.rect.width, 2)
        ph = round(page.rect.height, 2)
        spans = []
        text_len = 0

        for block in page.get_text("dict")["blocks"]:
            if block.get("type") == 1:
                # 图片块（我们统一用 get_images 处理，这里跳过避免结构歧义）
                continue
            for line in block.get("lines", []):
                for s in line.get("spans", []):
                    txt = s["text"]
                    if not txt.strip():
                        continue
                    bbox = s["bbox"]
                    weight, style = _style_from_font(s.get("flags", 0), s["font"])
                    spans.append({
                        "t": txt,
                        "x": round(bbox[0], 2),
                        "y": round(bbox[1], 2),
                        "w": round(bbox[2] - bbox[0], 2),
                        "h": round(bbox[3] - bbox[1], 2),
                        "size": round(s["size"], 2),
                        "font": s["font"],
                        "color": _css_color(s["color"]),
                        "weight": weight,
                        "style": style,
                    })
                    text_len += len(txt)

        # 内嵌图片（含图片块里的图），按 xref 去重
        imgs = []
        seen = set()
        for img in page.get_images(full=True):
            xref = img[0]
            if xref in seen:
                continue
            seen.add(xref)
            for r in page.get_image_rects(xref):
                imgs.append({
                    "xref": xref,
                    "x": round(r.x0, 2),
                    "y": round(r.y0, 2),
                    "w": round(r.x1 - r.x0, 2),
                    "h": round(r.y1 - r.y0, 2),
                })

        pages.append({
            "w": pw,
            "h": ph,
            "spans": spans,
            "imgs": imgs,
            "text_len": text_len,
        })

    meta = {
        "title": (doc.metadata or {}).get("title", "") or "",
        "author": (doc.metadata or {}).get("author", "") or "",
        "page_count": doc.page_count,
    }
    doc.close()
    return meta, pages


def extract_image(pdf_path: str, xref: int):
    """返回 (bytes, ext)。用于后端把内嵌图存成文件。"""
    doc = fitz.open(pdf_path)
    info = doc.extract_image(xref)
    doc.close()
    return info["image"], info["ext"].lstrip(".")


def render_page_image(pdf_path: str, pno: int, dpi: int = 100) -> bytes:
    """把某一页渲染成 PNG（仅用于文字极少的「图页」兜底）。"""
    doc = fitz.open(pdf_path)
    pix = doc[pno].get_pixmap(dpi=dpi)
    data = pix.tobytes("png")
    doc.close()
    return data
