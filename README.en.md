# 📚 Algorithm Books — Turn PDF textbooks into "scrollable, copyable" self-contained web pages

> One command converts any PDF (text-based / scanned) into an HTML reader with no external dependencies;
> plus a built-in static bookshelf + PDF.js viewer to read the original PDFs in place.

**Core pitch**: `git clone` → drop the PDF you want to read into the folder → one command → a
**scrollable, selectable/copyable, double-click-to-open** self-contained HTML (`converted/<book>/index.html`)
that references none of the repo's `lib/`, so it can be dropped onto any static server or GitHub Pages.

---

## ✨ Two reading modes

| Mode | Command / Entry | Best for | Copy text |
|------|------------|------|----------|
| **A. Converted HTML** | `python converter/convert.py your-book.pdf` | Long-term reading, copying snippets | ✅ Text-based PDFs are copyable natively; scanned PDFs become copyable after installing tesseract |
| **B. PDF.js original viewer** | Open `index.html` → click "PDF version" | Original layout, formulas | ✅ The text layer is made transparent but selectable |
| **Bookshelf gallery** | Open `index.html` | Browsing the shelf | — |

> Both modes are pure static: zero backend, zero CDN.

---

## 🚀 Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

- `pymupdf`: **required**, PDF parsing & rendering (provides `fitz`).
- `pillow` + `pytesseract`: **for OCR**, needed only if you want scanned PDFs to have copyable text.
- The repo ships `pypkgs/fitz` as a fallback; if you install the pip packages above, the pip version is used (either works).

### 2. Convert any PDF → self-contained HTML

```bash
# Most common: convert a single PDF (auto-detects "text-based / scanned")
python converter/convert.py my-book.pdf

# Specify output dir and book title
python converter/convert.py my-book.pdf -o ./out/my-book --title "My Book"

# Want a scanned book to be copyable? Install tesseract first (see "OCR notes" below), then enable OCR
python converter/convert.py scanned-book.pdf --ocr --lang chi_sim+eng
```

After conversion you get:

```
converted/my-book/
├── index.html        # self-contained: CSS/JS inlined, the hljs needed for code highlighting is copied in too
├── images/           # per-page images (scanned) or illustrations (text-based)
└── assets/           # highlight.min.* (text-based only)
```

Open `converted/my-book/index.html` in a browser to read (an HTTP server is recommended,
since some browsers block certain resources under `file://`).

### 3. Use the bookshelf gallery (PDF.js viewer)

```bash
python -m http.server 3000
# open http://localhost:3000/index.html in the browser
```

> ⚠️ You must serve over HTTP; the `file://` protocol is blocked by CORS.

---

## 🔤 OCR notes (the key to copyable text in scanned PDFs)

Scanned PDFs have no embedded text, so by default they are converted to "one high-res image per page",
**with text that cannot be selected/copied**. To make it copyable, you need OCR:

1. **Install the tesseract binary system-wide** and add it to `PATH`:
   - Windows: install the [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) package, and tick the Chinese pack `chi_sim`.
   - macOS: `brew install tesseract tesseract-lang`
   - Linux: `sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
2. Install the Python deps: `pip install pytesseract pillow` (already in `requirements.txt`).
3. Re-convert: `python converter/convert.py scanned-book.pdf --ocr`.

The converted scanned pages get an OCR text layer overlaid that is **aligned with the image, transparent but selectable** (`.ocr-layer`),
so scanned books can be Ctrl+C copied just like text-based books.

> No tesseract installed on this machine? No problem — the converter **gracefully degrades to plain images** and shows a hint at the top of the page on how to enable OCR.

---

## 📂 Project structure

```
算法书/
├── index.html              # [Gallery] bookshelf entry
├── viewer.html             # [Phase 1] PDF.js viewer
├── books.json              # book config (bookshelf + batch conversion)
├── converter/
│   └── convert.py          # [Phase 2] PDF → self-contained HTML converter (pure CLI)
├── requirements.txt        # pip dependency list
├── lib/                    # pdfjs + highlight.js for the bookshelf/viewer (not used by the converter)
├── css/  js/               # bookshelf & viewer styles / logic
├── pypkgs/                 # PyMuPDF fallback (gitignored, pip install recommended)
└── converted/              # conversion output (gitignored; only poster is deployed as a minimal demo)
    └── poster/             # text-based demo (deployed to GitHub Pages)
```

---

## 📖 Books included

| Title | Type | PDF | HTML |
|------|------|--------|---------|
| Poster | Text-based (1 page) | ✅ | ✅ Deployed (minimal demo) |
| 大话数据结构 (Data Structures in Plain Language) | Scanned | ✅ | Available after local conversion |
| 深入浅出程序设计竞赛（基础篇） (Competitive Programming from the Ground Up) | Scanned | ✅ | Available after local conversion |
| 算法竞赛（上册） (Algorithmic Competitions, Vol. 1) | Scanned | ✅ | Available after local conversion |
| 算法竞赛（下册） (Algorithmic Competitions, Vol. 2) | Scanned | ✅ | Available after local conversion |

> `converted/` is gitignored: **after clone, only the poster demo is visible online by default**;
> for the other books, run `python converter/convert.py --batch` locally to generate them (preserving the bookshelf gallery).

---

## 🛠 Tech stack

- **PDF rendering**: PDF.js 3.11 (zero CDN, bundled locally)
- **Code highlighting**: highlight.js 11.9
- **PDF conversion**: PyMuPDF 1.28 (converter core)
- **Pure static**: no backend, no framework, no build tooling

---

## 📋 Roadmap

- [x] **Phase 1**: static bookshelf + PDF.js viewer (scroll/page/TOC/code highlighting)
- [x] **Phase 2**: CLI converter productized (portable, self-contained, optional OCR)
- [ ] **Phase 3**: online service (web upload → convert → read online / download zip) — see `server/`

See [PROGRESS.md](./PROGRESS.md) and [handoff.md](./handoff.md) for details.

---

## 📄 License

MIT License
