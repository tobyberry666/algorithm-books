import sys
from pathlib import Path
ROOT = Path(r'F:\大一下文件\算法书')
sys.path.insert(0, str(ROOT / 'pypkgs'))

import fitz, json, os, re, base64, argparse, shutil

OUTPUT = ROOT / 'converted'
HLJS_CSS = '../../lib/highlight.min.css'
HLJS_JS = '../../lib/highlight.min.js'
CODE_KEYWORDS = re.compile(
    r'\b(int|void|char|float|double|if|for|while|return|class|struct|public|private|'
    r'static|const|#include|using|namespace|def|import|print|function|var|let|const|'
    r'scanf|printf|cout|cin|endl|main|bool|long|short|unsigned|signed|auto|break|'
    r'continue|else|switch|case|default|do|goto|sizeof|typedef|union|enum|extern|'
    r'virtual|override|new|delete|this|try|catch|throw|String|System|out|println|'
    r'package|public|private|protected|extends|implements|interface|abstract)\b'
)

def extract_outline(pdf):
    toc = pdf.get_toc()
    if not toc:
        return [], None
    flat = []
    for level, title, page in toc:
        flat.append({'level': level, 'title': title.strip(), 'page': page})
    return flat, toc

def is_code_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if line.startswith('    ') or line.startswith('\t'):
        return True
    if CODE_KEYWORDS.search(stripped):
        return True
    if re.match(r'^[\{\}]', stripped):
        return True
    return False

def extract_page_content(pdf, page_num, book_output_dir, page_idx):
    page = pdf[page_num]
    blocks = page.get_text('dict')['blocks']
    lines = []
    images = []
    for block in blocks:
        if block['type'] == 0:
            for line_data in block.get('lines', []):
                spans = line_data.get('spans', [])
                if not spans:
                    continue
                full_text = ''.join(s.get('text', '') for s in spans)
                if full_text.strip():
                    bbox = line_data['bbox']
                    font_size = spans[0].get('size', 12)
                    font_name = spans[0].get('font', 'sans-serif')
                    lines.append({
                        'text': full_text,
                        'y': bbox[1],
                        'x': bbox[0],
                        'size': font_size,
                        'bold': 'Bold' in font_name,
                    })
        elif block['type'] == 1:
            try:
                img_data = block.get('image')
                if img_data:
                    ext = block.get('ext', 'png')
                    fname = f'page{page_idx+1:03d}_{len(images)+1:02d}.{ext}'
                    fpath = book_output_dir / fname
                    fpath.write_bytes(img_data)
                    images.append({
                        'src': fname,
                        'y': block['bbox'][1],
                        'width': block['bbox'][2] - block['bbox'][0],
                    })
            except Exception:
                pass
    return lines, images

def lines_to_html(lines, images, page_idx, images_dir):
    html_parts = [f'<section class="page" id="page-{page_idx + 1}">']
    all_items = []
    for img in images:
        all_items.append(('img', img))
    for line in lines:
        all_items.append(('line', line))
    all_items.sort(key=lambda x: x[1]['y'])

    i = 0
    while i < len(all_items):
        item = all_items[i]
        if item[0] == 'img':
            img = item[1]
            html_parts.append(
                f'<div class="image-container">'
                f'<img src="images/{img["src"]}" style="max-width:{int(img["width"])}px" loading="lazy">'
                f'</div>'
            )
            i += 1
            continue

        line = item[1]
        if is_code_line(line['text']):
            code_lines = []
            j = i
            while j < len(all_items) and all_items[j][0] == 'line' and is_code_line(all_items[j][1]['text']):
                code_lines.append(all_items[j][1]['text'])
                j += 1
            if len(code_lines) >= 3:
                code_text = '\n'.join(code_lines).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                html_parts.append(f'<pre class="auto-fix" data-fix="自动识别代码块"><code>{code_text}</code></pre>')
                i = j
                continue

        text = line['text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        tag = 'p'
        if line.get('bold') and line.get('size', 12) > 14:
            tag = 'h4'
        if tag == 'h4':
            html_parts.append(f'<h4 class="auto-fix" data-fix="自动识别标题">{text}</h4>')
        else:
            html_parts.append(f'<p>{text}</p>')
        i += 1

    html_parts.append('</section>')
    return '\n'.join(html_parts)

def build_nav_html(flat_outline):
    if not flat_outline:
        return '<ul></ul>'
    result = ['<ul>']
    prev_level = 1
    for entry in flat_outline:
        level = entry['level']
        title = entry['title'].replace('&', '&amp;').replace('<', '&lt;')
        page = entry['page']
        if level > prev_level:
            result.append('<ul>')
        elif level < prev_level:
            for _ in range(prev_level - level):
                result.append('</ul></li>')
        elif prev_level > 0 and not result[-1].startswith('<ul'):
            result.append('</li>')
        result.append(f'<li class="nav-item lvl-{level}">')
        result.append(f'<a href="#page-{page}">{title}</a>')
        prev_level = level
    for _ in range(prev_level):
        result.append('</li></ul>')
    return '\n'.join(result)

PAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="{hljs_css}">
<style>
* {{margin:0;padding:0;box-sizing:border-box}}
body {{
  font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;
  font-size: 16px; line-height: 1.8; color: #333; display: flex; height:100vh;
}}
#sidebar {{
  width: 260px; flex-shrink:0; background:#f7f7f7; border-right:1px solid #ddd;
  overflow-y:auto; padding: 20px 0; height:100vh;
}}
#sidebar h2 {{font-size:15px; padding:0 14px 12px; border-bottom:1px solid #ddd; margin-bottom:8px;}}
#sidebar ul {{list-style:none; font-size:13px;}}
#sidebar ul ul {{padding-left:14px;}}
#sidebar li {{margin:0;}}
#sidebar .nav-item a {{
  display:block; padding:4px 14px; color:#555; text-decoration:none;
  border-left: 3px solid transparent; transition: all 0.15s;
}}
#sidebar .nav-item a:hover {{background:#e8e8e8; color:#333;}}
#sidebar .nav-item.lvl-1 a {{font-weight:600; font-size:14px;}}
#sidebar .nav-item.lvl-2 a {{padding-left:28px; font-size:12px;}}
#sidebar .nav-item.lvl-3 a {{padding-left:42px; font-size:12px; color:#777;}}
#content {{
  flex:1; overflow-y:auto; padding:32px 40px; min-width:0;
}}
#content section {{margin-bottom:28px; padding-bottom:20px; border-bottom:1px solid #eee;}}
#content p {{margin-bottom:6px; text-align:justify;}}
#content h4 {{font-size:17px; margin:14px 0 6px; font-weight:600;}}
#content pre {{
  background:#f6f8fa; border:1px solid #d1d5db; border-radius:6px;
  padding:12px 14px; margin:6px 0 14px; overflow-x:auto;
  font-family: 'Consolas','Courier New',monospace; font-size:13px; line-height:1.5;
}}
#content .image-container {{
  text-align:center; margin:10px 0;
}}
#content .image-container img {{
  max-width:100%; height:auto; border-radius:4px;
  box-shadow:0 1px 4px rgba(0,0,0,0.1);
}}
.auto-fix {{
  position:relative;
  border-left: 3px solid #f9a825;
  padding-left: 8px;
  border-radius: 0 4px 4px 0;
}}
.auto-fix::before {{
  content: "[" attr(data-fix) "]";
  display: inline-block;
  background: #fff3e0;
  color: #e65100;
  font-size: 10px;
  padding: 0 4px;
  margin-right: 4px;
  border-radius: 2px;
  border: 1px solid #ffcc80;
}}
@media (max-width:768px) {{
  body {{flex-direction:column;}}
  #sidebar {{width:100%; height:auto; border-right:none; border-bottom:1px solid #ddd;}}
  #content {{padding:16px;}}
}}
</style>
</head>
<body>
<nav id="sidebar">
  <h2>{title}</h2>
  {nav}
</nav>
<main id="content">
{content}
</main>
<script src="{hljs_js}"></script>
<script>hljs.highlightAll();</script>
</body>
</html>'''

def convert_pdf(pdf_path, book_id, title):
    print(f'Converting: {title}')
    doc = fitz.open(pdf_path)
    total = len(doc)
    flat_outline, raw_toc = extract_outline(doc)
    nav_html = build_nav_html(flat_outline)

    book_dir = OUTPUT / book_id
    images_dir = book_dir / 'images'
    book_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(exist_ok=True)

    pages_html = []
    for i in range(total):
        lines, images = extract_page_content(doc, i, images_dir, i)
        if lines or images:
            pages_html.append(lines_to_html(lines, images, i, images_dir))
        if (i + 1) % 50 == 0:
            print(f'  Page {i + 1}/{total}')

    doc.close()
    full_html = PAGE_TEMPLATE.format(
        title=title, hljs_css=HLJS_CSS, nav=nav_html,
        content='\n'.join(pages_html), hljs_js=HLJS_JS,
    )
    out_path = book_dir / 'index.html'
    out_path.write_text(full_html, encoding='utf-8')
    img_count = len(list(images_dir.glob('*.png')))
    html_size = out_path.stat().st_size / 1024
    img_total = sum(f.stat().st_size for f in images_dir.glob('*.png')) / 1024 / 1024
    print(f'  -> {out_path.relative_to(ROOT)}')
    print(f'  HTML: {html_size:.0f} KB, Images: {img_count} files, {img_total:.1f} MB total')
    return out_path

def main():
    parser = argparse.ArgumentParser(description='Convert PDF books to HTML')
    parser.add_argument('--book', help='Only convert book with this ID')
    args = parser.parse_args()

    books_json = ROOT / 'books.json'
    if not books_json.exists():
        print('books.json not found')
        sys.exit(1)
    with open(books_json, 'r', encoding='utf-8') as f:
        config = json.load(f)
    OUTPUT.mkdir(exist_ok=True)
    for book in config.get('books', []):
        if args.book and book['id'] != args.book:
            continue
        pdf_path = ROOT / book['file']
        if not pdf_path.exists():
            print(f'SKIP (not found): {pdf_path}')
            continue
        convert_pdf(str(pdf_path), book['id'], book['title'])
    print('\nDone!')

if __name__ == '__main__':
    main()
