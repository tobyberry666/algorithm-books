#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pdf2html — 把任意 PDF 转换成「可滚动 + 可复制」的自包含 HTML 阅读页。

特性
----
- 纯 CLI，不依赖任何写死的项目路径：任何人 clone 后放一本 PDF 进来即可转换。
- 自动识别「文字版 / 扫描版」：
    * 文字版：直接抽取结构化文本（标题 / 段落 / 代码块 / 配图），天然可选中复制。
    * 扫描版：每页渲染为高清图片；若本机装有 tesseract + 中文包，则叠加一层
      与图片对齐、透明但可被选中的 OCR 文字层 —— 于是扫描书也能复制文字。
- 输出完全自包含：CSS/JS 内联，代码高亮所需的 highlight.js 会一并复制到输出目录。
  不引用仓库根目录的 lib/，拿到手就能丢到任意静态服务器 / GitHub Pages。

用法
----
    # 转换单个 PDF（自动判断扫描/文字）
    python convert.py 我的书.pdf

    # 指定输出目录与书名
    python convert.py 我的书.pdf -o ./out/我的书 --title "我的书"

    # 扫描版强制开 OCR（需先装 tesseract，见 README）
    python convert.py 扫描书.pdf --ocr --lang chi_sim+eng

    # 用仓库现有的 books.json 批量重转（保留书架画廊）
    python convert.py --batch

依赖
----
    pip install -r requirements.txt
    （pymupdf 必装；pytesseract + pillow 用于 OCR，缺了扫描版退化为纯图片）
"""

import sys
import os
import re
import json
import argparse
import shutil
from pathlib import Path

# ---- 让脚本既支持「pip install pymupdf」也支持当前仓库的 pypkgs 兜底 ----
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
for _cand in (_REPO_ROOT / 'pypkgs',):
    if _cand.is_dir() and str(_cand) not in sys.path:
        sys.path.insert(0, str(_cand))
try:
    import fitz  # PyMuPDF
except ImportError:
    sys.stderr.write(
        "缺少依赖 fitz (PyMuPDF)。请先执行: pip install pymupdf\n"
    )
    sys.exit(1)

# OCR 相关依赖（可选）
try:
    import pytesseract
    from PIL import Image
    _HAS_OCR_DEPS = True
except Exception:
    _HAS_OCR_DEPS = False

# 代码块关键字（用于文字版启发式检测）
CODE_KEYWORDS = re.compile(
    r'\b(int|void|char|float|double|if|for|while|return|class|struct|public|private|'
    r'static|const|#include|using|namespace|def|import|print|function|var|let|'
    r'scanf|printf|cout|cin|endl|main|bool|long|short|unsigned|signed|auto|break|'
    r'continue|else|switch|case|default|do|goto|sizeof|typedef|union|enum|extern|'
    r'virtual|override|new|delete|this|try|catch|throw|String|System|out|println|'
    r'package|extends|implements|interface|abstract|template|typename|register|'
    r'volatile|unsigned)\b'
)

# --------------------------------------------------------------------------- #
# 小工具
# --------------------------------------------------------------------------- #
def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def resolve_lib_assets():
    """找到仓库自带的 highlight.js（用于文字版代码高亮）。找不到则返回 None。"""
    cand = _REPO_ROOT / 'lib'
    js = cand / 'highlight.min.js'
    css = cand / 'highlight.min.css'
    if js.exists() and css.exists():
        return js, css
    return None


def copy_hljs(out_assets):
    """把 highlight.js 复制进输出目录，实现自包含。成功返回 True。"""
    pair = resolve_lib_assets()
    if not pair:
        return False
    js, css = pair
    out_assets.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(js, out_assets / 'highlight.min.js')
    shutil.copyfile(css, out_assets / 'highlight.min.css')
    return True


# --------------------------------------------------------------------------- #
# 模式判定
# --------------------------------------------------------------------------- #
def detect_mode(doc, sample=10):
    """抽样前 N 页，按平均字符数判断是文字版还是扫描版。"""
    total = len(doc)
    n = min(sample, total)
    chars = 0
    for i in range(n):
        chars += len(doc[i].get_text('text') or '')
    avg = chars / n if n else 0
    return 'text' if avg >= 8 else 'scan'


# --------------------------------------------------------------------------- #
# TOC（目录）生成
# --------------------------------------------------------------------------- #
def build_nav(outline_toc, anchor_for_page):
    """
    根据 PDF outline 生成侧边栏目录。
    outline_toc: fitz get_toc() 的结果 [(level, title, page), ...]
    anchor_for_page: 把页码映射成锚点 id 的函数（文字版/扫描版不同）
    返回 HTML 字符串。
    """
    if not outline_toc:
        return '<ul><li class="nav-item"><a href="#top">（本书无目录）</a></li></ul>'

    items = []
    for level, title, page in outline_toc:
        safe_title = html_escape(title.strip())
        anchor = anchor_for_page(page)
        items.append((level, safe_title, anchor))

    # 用栈生成正确嵌套的 <ul>/<li>
    html = ['<ul>']
    stack = [1]
    for level, title, anchor in items:
        level = max(1, min(level, 6))
        while stack and stack[-1] > level:
            html.append('</li></ul>')
            stack.pop()
        if stack and stack[-1] < level:
            html.append('<ul>')
            stack.append(level)
        html.append(
            f'<li class="nav-item lvl-{level}">'
            f'<a href="#{anchor}">{title}</a>'
        )
    while len(stack) > 1:
        html.append('</li></ul>')
        stack.pop()
    html.append('</li></ul>')
    return '\n'.join(html)


# --------------------------------------------------------------------------- #
# 文字版转换
# --------------------------------------------------------------------------- #
def is_code_line(text):
    s = text.strip()
    if not s:
        return False
    if text.startswith('    ') or text.startswith('\t'):
        return True
    if CODE_KEYWORDS.search(s):
        return True
    if re.match(r'^[{}]', s):
        return True
    return False


def convert_text_page(page, images_dir, page_idx, img_counter):
    """抽取单页文字，返回 (html_fragment, image_count)。"""
    blocks = page.get_text('dict')['blocks']
    lines = []
    image_files = []
    for block in blocks:
        if block['type'] == 0:
            for line_data in block.get('lines', []):
                spans = line_data.get('spans', [])
                if not spans:
                    continue
                full = ''.join(sp.get('text', '') for sp in spans)
                if not full.strip():
                    continue
                bbox = line_data['bbox']
                font = spans[0].get('font', '')
                lines.append({
                    'text': full,
                    'y': bbox[1],
                    'size': spans[0].get('size', 12),
                    'bold': 'Bold' in font,
                })
        elif block['type'] == 1:
            try:
                img_data = block.get('image')
                if img_data:
                    ext = block.get('ext', 'png')
                    img_counter[0] += 1
                    fname = f'fig-{page_idx+1:03d}-{img_counter[0]:02d}.{ext}'
                    (images_dir / fname).write_bytes(img_data)
                    image_files.append(fname)
            except Exception:
                pass

    # 按 y 坐标排序图文
    items = [('line', l) for l in lines] + [('img', f) for f in image_files]
    items.sort(key=lambda x: x[1]['y'] if x[0] == 'line' else 0)

    parts = [f'<section class="page" id="page-{page_idx+1}">']
    i = 0
    while i < len(items):
        kind, val = items[i]
        if kind == 'img':
            parts.append(
                f'<div class="image-container">'
                f'<img src="images/{val}" loading="lazy" alt="配图"></div>'
            )
            i += 1
            continue
        # 代码块合并
        if is_code_line(val['text']):
            code = []
            j = i
            while j < len(items) and items[j][0] == 'line' and is_code_line(items[j][1]['text']):
                code.append(items[j][1]['text'])
                j += 1
            if len(code) >= 3:
                code_text = html_escape('\n'.join(code))
                parts.append(
                    f'<pre class="code-block"><code>{code_text}</code></pre>'
                )
                i = j
                continue
        text = html_escape(val['text'])
        if val.get('bold') and val.get('size', 12) > 14:
            parts.append(f'<h3 class="auto-fix" data-fix="自动识别标题">{text}</h3>')
        else:
            parts.append(f'<p>{text}</p>')
        i += 1
    parts.append('</section>')
    return '\n'.join(parts), len(image_files)


# --------------------------------------------------------------------------- #
# 扫描版转换（图片 + 可选 OCR）
# --------------------------------------------------------------------------- #
def ocr_page(img, lang):
    """对 PIL 图片做 OCR，返回归一化后的词列表：
       [left%, top%, width%, height%, text]（百分比相对图片尺寸）。"""
    data = pytesseract.image_to_data(
        img, lang=lang, output_type=pytesseract.Output.DICT
    )
    W, H = img.size
    words = []
    n = len(data.get('text', []))
    for k in range(n):
        conf = int(data['conf'][k])
        txt = (data['text'][k] or '').strip()
        if conf < 0 or not txt:
            continue
        left = data['left'][k] / W * 100
        top = data['top'][k] / H * 100
        width = data['width'][k] / W * 100
        height = data['height'][k] / H * 100
        words.append([round(left, 2), round(top, 2),
                      round(width, 2), round(height, 2), txt])
    return words


def convert_scan_page(page, images_dir, page_idx, dpi, do_ocr, lang):
    """渲染单页为 PNG；若启用 OCR 返回词列表，否则 None。"""
    pix = page.get_pixmap(dpi=dpi)
    fname = f'page-{page_idx+1:03d}.png'
    pix.save(str(images_dir / fname))

    words = None
    if do_ocr and _HAS_OCR_DEPS:
        try:
            img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
            words = ocr_page(img, lang)
        except Exception as e:
            sys.stderr.write(f'  [warn] 第 {page_idx+1} 页 OCR 失败: {e}\n')
            words = None
    return fname, words


# --------------------------------------------------------------------------- #
# 组装最终 HTML
# --------------------------------------------------------------------------- #
PAGE_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
  font-size: 16px; line-height: 1.85; color: #2b2b2b; display: flex; min-height: 100vh;
  background: #fff;
}
#sidebar {
  width: 268px; flex-shrink: 0; background: #f7f7f9; border-right: 1px solid #e5e5e8;
  overflow-y: auto; padding: 18px 0; height: 100vh; position: sticky; top: 0;
}
#sidebar h2 { font-size: 15px; padding: 0 16px 12px; border-bottom: 1px solid #e5e5e8; margin-bottom: 8px; word-break: break-all; }
#sidebar ul { list-style: none; font-size: 13px; }
#sidebar li { margin: 0; }
#sidebar .nav-item > a {
  display: block; padding: 5px 16px; color: #555; text-decoration: none;
  border-left: 3px solid transparent; transition: all .15s;
}
#sidebar .nav-item > a:hover { background: #ececf0; color: #222; }
#sidebar .nav-item.active > a { background: #e6ebff; color: #2540b8; border-left-color: #4b6bff; font-weight: 600; }
#sidebar .lvl-1 > a { font-weight: 600; font-size: 14px; }
#sidebar .lvl-2 > a { padding-left: 30px; font-size: 12.5px; }
#sidebar .lvl-3 > a { padding-left: 44px; font-size: 12px; color: #777; }
#content { flex: 1; overflow-y: auto; padding: 36px 48px; min-width: 0; max-width: 100%; }
#content section { margin-bottom: 30px; padding-bottom: 22px; border-bottom: 1px solid #f0f0f0; }
#content p { margin-bottom: 8px; text-align: justify; }
#content h3 { font-size: 18px; margin: 16px 0 8px; font-weight: 600; }
#content pre.code-block {
  background: #f6f8fa; border: 1px solid #d1d5db; border-radius: 6px;
  padding: 12px 14px; margin: 8px 0 16px; overflow-x: auto;
  font-family: "JetBrains Mono", Consolas, "Courier New", monospace; font-size: 13px; line-height: 1.55;
}
#content .image-container { text-align: center; margin: 12px 0; }
#content .image-container img { max-width: 100%; height: auto; border-radius: 4px; box-shadow: 0 1px 5px rgba(0,0,0,.12); }
.auto-fix { position: relative; border-left: 3px solid #f9a825; padding-left: 8px; border-radius: 0 4px 4px 0; }
.auto-fix::before {
  content: "[" attr(data-fix) "]"; display: inline-block; background: #fff3e0; color: #e65100;
  font-size: 10px; padding: 0 4px; margin-right: 4px; border-radius: 2px; border: 1px solid #ffcc80;
}
.note { background: #fff8e1; border: 1px solid #ffe082; border-radius: 6px; padding: 10px 14px; margin: 16px 0; font-size: 13px; color: #6d4c00; }
/* 扫描页 + OCR 文字层 */
.page-scan { position: relative; margin: 0 auto 24px; max-width: 900px; }
.page-scan > img { display: block; width: 100%; height: auto; border-radius: 4px; box-shadow: 0 1px 6px rgba(0,0,0,.15); background: #fff; }
.ocr-layer { position: absolute; inset: 0; pointer-events: auto; overflow: hidden; }
.ocr-layer span {
  position: absolute; color: transparent; white-space: pre; cursor: text;
  user-select: text; -webkit-user-select: text; transform-origin: 0 0;
}
.ocr-layer ::selection { background: rgba(40, 90, 255, .28); }
#menu-toggle { display: none; }
@media (max-width: 820px) {
  body { flex-direction: column; }
  #sidebar { width: 100%; height: auto; position: static; border-right: none; border-bottom: 1px solid #e5e5e8; max-height: 40vh; }
  #content { padding: 18px; }
}
"""

PAGE_JS = """
// 目录滚动高亮
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('#sidebar .nav-item > a'));
  var map = {};
  links.forEach(function (a) {
    var id = a.getAttribute('href').slice(1);
    var el = document.getElementById(id);
    if (el) map[id] = a.parentElement;
  });
  var targets = Object.keys(map).map(function (id) { return document.getElementById(id); });
  function onScroll() {
    var pos = window.scrollY + 120;
    var cur = null;
    targets.forEach(function (el) { if (el && el.offsetTop <= pos) cur = el.id; });
    links.forEach(function (a) { a.parentElement.classList.remove('active'); });
    if (cur && map[cur]) map[cur].classList.add('active');
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // 扫描版：懒加载 OCR 文字层
  var ocrRaw = document.getElementById('ocr-data');
  if (ocrRaw) {
    var ocr = JSON.parse(ocrRaw.textContent);
    var layers = Array.prototype.slice.call(document.querySelectorAll('.ocr-layer'));
    function build(layer) {
      var pid = layer.getAttribute('data-page');
      var words = ocr[pid];
      if (!words) return;
      var frag = document.createDocumentFragment();
      words.forEach(function (w) {
        var s = document.createElement('span');
        s.style.left = w[0] + '%'; s.style.top = w[1] + '%';
        s.style.width = w[2] + '%'; s.style.height = w[3] + '%';
        s.textContent = w[4];
        frag.appendChild(s);
      });
      layer.appendChild(frag);
      layer.setAttribute('data-built', '1');
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && !e.target.getAttribute('data-built')) build(e.target);
      });
    }, { rootMargin: '300px' });
    layers.forEach(function (l) { io.observe(l); });
  }
})();
"""


def build_html(title, nav_html, content_html, ocr_data, hljs_on, note_html=''):
    ocr_script = ''
    if ocr_data is not None:
        ocr_script = '<script id="ocr-data" type="application/json">' + json.dumps(
            ocr_data, ensure_ascii=False) + '</script>'
    hl_css = '<link rel="stylesheet" href="assets/highlight.min.css">' if hljs_on else ''
    hl_js = '<script src="assets/highlight.min.js"></script>' if hljs_on else ''
    hl_init = '<script>if (window.hljs) hljs.highlightAll();</script>' if hljs_on else ''
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_escape(title)}</title>
{hl_css}
<style>{PAGE_CSS}</style>
</head>
<body id="top">
<nav id="sidebar">
  <h2>{html_escape(title)}</h2>
  {nav_html}
</nav>
<main id="content">
{note_html}
{content_html}
</main>
{ocr_script}
{hl_js}
<script>{PAGE_JS}</script>
{hl_init}
</body>
</html>"""
    return html


# --------------------------------------------------------------------------- #
# 主转换流程
# --------------------------------------------------------------------------- #
def convert_pdf(pdf_path, out_dir, title, dpi, do_ocr, lang):
    doc = fitz.open(pdf_path)
    total = len(doc)
    mode = detect_mode(doc)
    print(f'[模式] {title} -> 检测为「{mode}」版（共 {total} 页）')

    out_dir = Path(out_dir)
    images_dir = out_dir / 'images'
    assets_dir = out_dir / 'assets'
    out_dir.mkdir(parents=True, exist_ok=True)
    if images_dir.exists():
        shutil.rmtree(images_dir)
    images_dir.mkdir(parents=True)

    toc = doc.get_toc()
    ocr_data = None

    if mode == 'text':
        hljs_on = copy_hljs(assets_dir)
        counter = [0]
        pages_html = []
        for i in range(total):
            frag, _ = convert_text_page(doc[i], images_dir, i, counter)
            pages_html.append(frag)
            if (i + 1) % 50 == 0:
                print(f'  已处理 {i + 1}/{total}')
        nav = build_nav(toc, lambda p: f'page-{p}')
        html = build_html(title, nav, '\n'.join(pages_html), None, hljs_on)
        note = ''
    else:
        # 扫描版
        hljs_on = False
        ocr_data = {} if (do_ocr and _HAS_OCR_DEPS) else None
        if do_ocr and not _HAS_OCR_DEPS:
            print('  [提示] 未检测到 pytesseract/Pillow，OCR 已禁用，扫描页仅可看图不可复制。')
        pages_html = []
        for i in range(total):
            fname, words = convert_scan_page(doc[i], images_dir, i, dpi, do_ocr, lang)
            if ocr_data is not None:
                ocr_data[str(i + 1)] = words or []
            anchor = f'page-{i + 1}'
            if words:
                pages_html.append(
                    f'<div class="page-scan" id="{anchor}">'
                    f'<img src="images/{fname}" loading="lazy" alt="第 {i+1} 页">'
                    f'<div class="ocr-layer" data-page="{i+1}"></div></div>'
                )
            else:
                pages_html.append(
                    f'<div class="page-scan" id="{anchor}">'
                    f'<img src="images/{fname}" loading="lazy" alt="第 {i+1} 页"></div>'
                )
            if (i + 1) % 50 == 0:
                print(f'  已处理 {i + 1}/{total}')
        nav = build_nav(toc, lambda p: f'page-{p}')
        if ocr_data is not None:
            note = ''
        else:
            note = ('<div class="note">本书为扫描版，当前未启用 OCR，页面文字<strong>不可复制</strong>。'
                    '在本机安装 <code>tesseract</code> + 中文语言包后，用 '
                    '<code>python convert.py 本书.pdf --ocr</code> 重新转换即可叠加可复制的文字层。</div>')
        html = build_html(title, nav, '\n'.join(pages_html), ocr_data, hljs_on, note)

    doc.close()
    (out_dir / 'index.html').write_text(html, encoding='utf-8')

    # 统计
    img_n = len(list(images_dir.glob('*.png')))
    html_kb = (out_dir / 'index.html').stat().st_size / 1024
    img_mb = sum(f.stat().st_size for f in images_dir.glob('*.png')) / 1024 / 1024
    ocr_n = sum(len(v) for v in (ocr_data or {}).values()) if ocr_data else 0
    print(f'  -> 输出: {out_dir / "index.html"}')
    print(f'  HTML {html_kb:.0f} KB | 图片 {img_n} 张 {img_mb:.1f} MB'
          + (f' | OCR 词 {ocr_n}' if ocr_n else ''))
    return out_dir


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description='把任意 PDF 转换成可滚动、可复制的自包含 HTML 阅读页')
    ap.add_argument('pdf', nargs='?', help='要转换的 PDF 文件路径')
    ap.add_argument('-o', '--output', help='输出目录（默认 ./converted/<文件名>)')
    ap.add_argument('--title', help='书名（默认取 PDF 文件名）')
    ap.add_argument('--dpi', type=int, default=110, help='扫描版渲染 DPI（默认 110）')
    ap.add_argument('--ocr', action='store_true', help='扫描版启用 OCR 文字层（需 tesseract）')
    ap.add_argument('--lang', default='chi_sim+eng', help='OCR 语言（默认 chi_sim+eng）')
    ap.add_argument('--batch', action='store_true',
                    help='读取仓库 books.json 批量重转（保留书架画廊）')
    args = ap.parse_args()

    if args.batch:
        books_json = _REPO_ROOT / 'books.json'
        if not books_json.exists():
            sys.stderr.write('未找到 books.json，无法 --batch\n')
            sys.exit(1)
        cfg = json.loads(books_json.read_text(encoding='utf-8'))
        for b in cfg.get('books', []):
            pdf = _REPO_ROOT / b['file']
            if not pdf.exists():
                print(f'SKIP（缺失）: {pdf}')
                continue
            out = _REPO_ROOT / 'converted' / b['id']
            convert_pdf(str(pdf), str(out), b.get('title', b['id']),
                        args.dpi, args.ocr, args.lang)
        print('\n批量转换完成！')
        return

    if not args.pdf:
        ap.print_help()
        sys.stderr.write('\n错误：请提供 PDF 路径，或使用 --batch。\n')
        sys.exit(1)

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        sys.stderr.write(f'找不到 PDF: {pdf_path}\n')
        sys.exit(1)

    title = args.title or pdf_path.stem
    out_dir = args.output or (Path('converted') / pdf_path.stem)
    convert_pdf(str(pdf_path), str(out_dir), title, args.dpi, args.ocr, args.lang)
    print('\n完成！用浏览器打开输出目录的 index.html 即可阅读（建议通过 http 服务器）。')


if __name__ == '__main__':
    main()
