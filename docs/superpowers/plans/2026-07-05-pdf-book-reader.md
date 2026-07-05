 # PDF Book Reader — Implementation Plan

 > **For agentic workers:** Use inline execution (executing-plans) for this implementation.

 **Goal:** Build a pure-static HTML/JS PDF bookshelf reader with scrolling+flip modes, text layer copy, and code highlighting.

 **Architecture:** Two-page app — `index.html` (bookshelf) and `viewer.html` (reader). PDF.js renders each page to Canvas with textLayer overlay. highlight.js auto-detects code blocks. No server, no npm, no build tools.

 **Tech Stack:** vanilla JS (ES modules), PDF.js, highlight.js

 **Root:** `F:\大一下文件\算法书`

 ## Global Constraints

 - All files under `F:\大一下文件\算法书` (cwd)
 - Zero server dependencies — `file://` protocol must work
 - PDF.js and highlight.js vendored in `lib/` not CDN
 - Chinese text must be selectable/copyable
 - Both scroll and flip reading modes

 ---

 ### Task 1: Project Scaffolding

 **Files:**
 - Create all directories under `F:\大一下文件\算法书`

 - [ ] **Step 1: Create directory structure**

 Create all needed directories in one shot:

 ```powershell
 New-Item -ItemType Directory -Force -Path "F:\大一下文件\算法书\css", "F:\大一下文件\算法书\js", "F:\大一下文件\算法书\lib\pdfjs", "F:\大一下文件\算法书\books"
 ```

 - [ ] **Step 2: Create empty placeholder files**

 Create empty files to populate later:

 ```powershell
 New-Item -ItemType File -Force -Path "F:\大一下文件\算法书\index.html", "F:\大一下文件\算法书\viewer.html", "F:\大一下文件\算法书\books.json", "F:\大一下文件\算法书\css\bookshelf.css", "F:\大一下文件\算法书\css\viewer.css", "F:\大一下文件\算法书\js\bookshelf.js", "F:\大一下文件\算法书\js\viewer.js", "F:\大一下文件\算法书\js\toc.js", "F:\大一下文件\算法书\js\toolbar.js", "F:\大一下文件\算法书\js\utils.js"
 ```

 - [ ] **Step 3: Verify structure**

 ```powershell
 Get-ChildItem -Recurse -Name "F:\大一下文件\算法书\css", "F:\大一下文件\算法书\js", "F:\大一下文件\算法书\lib", "F:\大一下文件\算法书\books"
 ```

 ---

 ### Task 2: Download PDF.js and highlight.js

 **Files:**
 - Create: `lib/pdfjs/pdf.min.mjs`, `lib/pdfjs/pdf.worker.min.mjs`, `lib/pdfjs/pdf.min.mjs.map`, `lib/pdfjs/pdf.worker.min.mjs.map`
 - Create: `lib/highlight.min.js`, `lib/highlight.min.css` (or single-file)

 **Interfaces:**
 - Produces: `lib/pdfjs/pdf.min.mjs` — the PDF.js library entry point. `pdfjsLib.getDocument()` returns a `PDFDocumentLoadingTask` that resolves with `pdf.numPages`, `pdf.getPage(n)`, `pdf.getOutline()`.
 - Produces: `lib/pdfjs/pdf.worker.min.mjs` — the PDF.js Web Worker (referenced by path from pdf.min.mjs workerSrc config).
 - Produces: `lib/highlight.min.js` — `hljs.highlightElement(element)` for auto-detection highlighting.

 - [ ] **Step 1: Download PDF.js prebuilt distribution**

 Download the latest pdfjs-dist release from the official CDN. Use the stable v3.x or v4.x legacy build:

 ```powershell
 curl.exe -L -o "$env:TEMP\pdfjs.zip" "https://github.com/nicbarker/pdfjs-dist/archive/refs/heads/legacy.zip" 2>&1
 ```
 If unavailable, fallback to npm-based approach:

 ```powershell
 npm pack pdfjs-dist@3.11.174 --pack-destination "$env:TEMP" 2>&1
 ```
 Extract `build/pdf.min.mjs` and `build/pdf.worker.min.mjs` to `lib/pdfjs/`.

 - [ ] **Step 2: Download highlight.js single-file build**

 ```powershell
 curl.exe -L -o "F:\大一下文件\算法书\lib\highlight.min.js" "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js" 2>&1
 ```

 Download a theme CSS:

 ```powershell
 curl.exe -L -o "F:\大一下文件\算法书\lib\highlight.min.css" "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css" 2>&1
 ```

 - [ ] **Step 3: Verify downloads exist**

 ```powershell
 Get-ChildItem "F:\大一下文件\算法书\lib" -Recurse | Select-Object Name, Length
 ```

 ---

 ### Task 3: books.json and utils.js

 **Files:**
 - Create: `books.json`
 - Create: `js/utils.js`

 **Interfaces:**
 - Produces `books.json`: Array of book objects with `id`, `title`, `author`, `file` (relative path to PDF), optional `cover` (relative path to image).
 - Produces `js/utils.js`:
   - `getQueryParam(name)` — reads a URL query parameter, returns string or null.
   - `getBookConfig(bookId)` — fetches `books.json`, returns the matching book object by `id`.
   - `saveThumbnail(bookId, dataUrl)` — stores a base64 thumbnail in localStorage.
   - `getThumbnail(bookId)` — retrieves thumbnail from localStorage, returns dataUrl or null.
   - `updateUrlHash(params)` — updates `location.hash` with key=value pairs (e.g., `page=42`, `mode=scroll`).
   - `getUrlHash()` — parses `location.hash` into an object `{page, mode}`.

 - [ ] **Step 1: Write `books.json`**

 ```json
 {
   "books": [
     {
       "id": "dahua-datastructure",
       "title": "大话数据结构",
       "author": "程杰",
       "file": "books/大话数据结构 (程杰) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
     },
     {
       "id": "shen-ru-qian-chu",
       "title": "深入浅出程序设计竞赛（基础篇）",
       "author": "汪楚奇",
       "file": "books/深入浅出程序设计竞赛（基础篇） (汪楚奇) (Z-Library).pdf"
     },
     {
       "id": "algorithm-contest-1",
       "title": "算法竞赛（上册）",
       "author": "罗勇军，郭卫斌",
       "file": "books/算法竞赛（上册） (罗勇军，郭卫斌) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
     },
     {
       "id": "algorithm-contest-2",
       "title": "算法竞赛（下册）",
       "author": "罗勇军，郭卫斌",
       "file": "books/算法竞赛（下册） (罗勇军，郭卫斌) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
     }
   ]
 }
 ```

 - [ ] **Step 2: Write `js/utils.js`**

 ```javascript
 // utils.js — Shared helpers

 export function getQueryParam(name) {
   const params = new URLSearchParams(window.location.search);
   return params.get(name);
 }

 let _booksConfig = null;

 export async function getBookConfig(bookId) {
   if (!_booksConfig) {
     const resp = await fetch('books.json');
     _booksConfig = await resp.json();
   }
   return _booksConfig.books.find(b => b.id === bookId) || null;
 }

 export async function getAllBooks() {
   if (!_booksConfig) {
     const resp = await fetch('books.json');
     _booksConfig = await resp.json();
   }
   return _booksConfig.books;
 }

 export function saveThumbnail(bookId, dataUrl) {
   try {
     localStorage.setItem(`thumb_${bookId}`, dataUrl);
   } catch (e) { /* storage full, ignore */ }
 }

 export function getThumbnail(bookId) {
   return localStorage.getItem(`thumb_${bookId}`) || null;
 }

 export function updateUrlHash(params) {
   const current = getUrlHash();
   const merged = { ...current, ...params };
   const parts = [];
   for (const [k, v] of Object.entries(merged)) {
     if (v !== undefined && v !== null) parts.push(`${k}=${v}`);
   }
   window.location.hash = parts.join('&');
 }

 export function getUrlHash() {
   const result = {};
   const raw = window.location.hash.replace(/^#/, '');
   if (!raw) return result;
   for (const part of raw.split('&')) {
     const [k, v] = part.split('=');
     result[k] = v;
   }
   return result;
 }
 ```

 - [ ] **Step 3: Verify `books.json` is valid JSON and copy PDFs to books/ directory if not already present**

 ```powershell
 python -c "import json; json.load(open(r'F:\大一下文件\算法书\books.json')); print('OK')"
 ```

 The PDFs are already in `F:\大一下文件\算法书\` — they will be referenced by path from `books/` directory. Since the books are in the workspace root, update file paths in `books.json` to point to `../`:

 Change each `"file"` to use `"../文件名.pdf"` (one level up since books.json is in root and PDFs are also in root).

 ---

 ### Task 4: Bookshelf Page

 **Files:**
 - Write: `index.html`
 - Write: `css/bookshelf.css`
 - Write: `js/bookshelf.js`

 **Interfaces:**
 - Consumes: `utils.js` — `getAllBooks()`, `getThumbnail()`, `saveThumbnail()`
 - Produces: A grid of book cards. Clicking a card navigates to `viewer.html?book=<id>`. Each card shows cover thumbnail or fallback text.

 - [ ] **Step 1: Write `index.html`**

 ```html
 <!DOCTYPE html>
 <html lang="zh-CN">
 <head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>算法书阅读器</title>
   <link rel="stylesheet" href="css/bookshelf.css">
 </head>
 <body>
   <header>
     <h1>算法书阅读器</h1>
   </header>
   <main id="bookshelf">
     <div class="loading">加载中...</div>
   </main>
   <script type="module" src="js/bookshelf.js"></script>
 </body>
 </html>
 ```

 - [ ] **Step 2: Write `css/bookshelf.css`**

 ```css
 * { margin: 0; padding: 0; box-sizing: border-box; }
 body {
   font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
   background: #f5f5f5;
   color: #333;
   min-height: 100vh;
 }
 header {
   background: #fff;
   padding: 24px 32px;
   border-bottom: 1px solid #e0e0e0;
 }
 header h1 { font-size: 24px; font-weight: 600; }
 #bookshelf {
   display: grid;
   grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
   gap: 24px;
   padding: 32px;
   max-width: 1200px;
   margin: 0 auto;
 }
 .book-card {
   background: #fff;
   border-radius: 8px;
   overflow: hidden;
   box-shadow: 0 1px 3px rgba(0,0,0,0.1);
   cursor: pointer;
   transition: box-shadow 0.2s, transform 0.2s;
 }
 .book-card:hover {
   box-shadow: 0 4px 12px rgba(0,0,0,0.15);
   transform: translateY(-2px);
 }
 .book-cover {
   width: 100%;
   aspect-ratio: 3/4;
   object-fit: cover;
   background: #e8e8e8;
   display: flex;
   align-items: center;
   justify-content: center;
 }
 .book-cover.no-image {
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
   color: #fff;
   font-size: 18px;
   font-weight: 600;
   text-align: center;
   padding: 16px;
 }
 .book-info {
   padding: 12px 16px;
 }
 .book-info .title {
   font-size: 16px;
   font-weight: 600;
   margin-bottom: 4px;
   overflow: hidden;
   text-overflow: ellipsis;
   white-space: nowrap;
 }
 .book-info .author {
   font-size: 13px;
   color: #888;
 }
 .loading {
   grid-column: 1 / -1;
   text-align: center;
   padding: 48px;
   color: #999;
 }
 @media (max-width: 600px) {
   #bookshelf { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 16px; padding: 16px; }
 }
 ```

 - [ ] **Step 3: Write `js/bookshelf.js`**

 ```javascript
 import { getAllBooks, getThumbnail, saveThumbnail } from './utils.js';

 const shelf = document.getElementById('bookshelf');

 async function generateCover(book) {
   const cached = getThumbnail(book.id);
   if (cached) return cached;

   try {
     const loadingTask = pdfjsLib.getDocument(book.file);
     const pdf = await loadingTask.promise;
     const page = await pdf.getPage(1);
     const viewport = page.getViewport({ scale: 0.5 });
     const canvas = document.createElement('canvas');
     const ctx = canvas.getContext('2d');
     canvas.width = viewport.width;
     canvas.height = viewport.height;
     await page.render({ canvasContext: ctx, viewport }).promise;
     const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
     saveThumbnail(book.id, dataUrl);
     return dataUrl;
   } catch (e) {
     return null;
   }
 }

 function createBookCard(book, coverUrl) {
   const card = document.createElement('div');
   card.className = 'book-card';

   const cover = document.createElement('div');
   cover.className = 'book-cover';
   if (coverUrl) {
     const img = document.createElement('img');
     img.src = coverUrl;
     img.className = 'book-cover';
     img.alt = book.title;
     cover.appendChild(img);
   } else {
     cover.classList.add('no-image');
     cover.textContent = book.title;
   }

   const info = document.createElement('div');
   info.className = 'book-info';
   info.innerHTML = `<div class="title">${book.title}</div><div class="author">${book.author || ''}</div>`;

   card.appendChild(cover);
   card.appendChild(info);

   card.addEventListener('click', () => {
     window.location.href = `viewer.html?book=${encodeURIComponent(book.id)}`;
   });

   return card;
 }

 async function init() {
   try {
     const books = await getAllBooks();
     shelf.innerHTML = '';

     for (const book of books) {
       const coverUrl = await generateCover(book);
       const card = createBookCard(book, coverUrl);
       shelf.appendChild(card);
     }
   } catch (e) {
     shelf.innerHTML = '<div class="loading">加载失败，请检查 books.json 配置</div>';
   }
 }

 init();
 ```

 - [ ] **Step 4: Verify — open `index.html` in browser, expect to see book cards with covers generated**

 ---

 ### Task 5: Viewer Page Structure

 **Files:**
 - Write: `viewer.html`
 - Write: `css/viewer.css`

 **Interfaces:**
 - Produces: HTML skeleton with three zones: `#sidebar` (toc), `#pdf-container` (rendering), `#toolbar`
 - Consumes: URL param `book` for which PDF to load

 - [ ] **Step 1: Write `viewer.html`**

 ```html
 <!DOCTYPE html>
 <html lang="zh-CN">
 <head>
   <meta charset="UTF-8">
   <meta name="viewport" content="width=device-width, initial-scale=1.0">
   <title>阅读器</title>
   <link rel="stylesheet" href="css/viewer.css">
   <link rel="stylesheet" href="lib/highlight.min.css">
 </head>
 <body>
   <div id="toolbar">
     <button id="btn-back" title="返回书架">&larr;</button>
     <span id="book-title">加载中...</span>
     <div class="toolbar-right">
       <button id="btn-toc" title="目录">&#9776;</button>
       <button id="btn-mode" title="切换阅读模式">&#9776;</button>
       <span id="page-indicator">- / -</span>
     </div>
   </div>

   <div id="main-area">
     <div id="sidebar">
       <div id="toc-container">
         <div id="toc-loading">加载目录...</div>
       </div>
     </div>
     <div id="pdf-container">
       <div id="pdf-loading">加载中...</div>
     </div>
   </div>

   <div id="page-nav">
     <button id="btn-prev" title="上一页">&larr;</button>
     <span>页码跳转：<input type="number" id="page-input" min="1" value="1"></span>
     <button id="btn-next" title="下一页">&rarr;</button>
   </div>

   <script type="module" src="js/viewer.js"></script>
 </body>
 </html>
 ```

 - [ ] **Step 2: Write `css/viewer.css`**

 ```css
 * { margin: 0; padding: 0; box-sizing: border-box; }
 html, body { height: 100%; overflow: hidden; }
 body {
   font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
   display: flex;
   flex-direction: column;
   background: #525659;
 }
 #toolbar {
   display: flex;
   align-items: center;
   gap: 12px;
   padding: 8px 16px;
   background: #323639;
   color: #fff;
   flex-shrink: 0;
   height: 44px;
 }
 #toolbar button {
   background: none;
   border: 1px solid #555;
   color: #fff;
   padding: 4px 10px;
   border-radius: 4px;
   cursor: pointer;
   font-size: 16px;
 }
 #toolbar button:hover { background: #444; }
 #book-title { flex: 1; font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
 .toolbar-right { display: flex; align-items: center; gap: 8px; }
 #page-indicator { font-size: 13px; color: #aaa; }

 #main-area {
   display: flex;
   flex: 1;
   overflow: hidden;
 }
 #sidebar {
   width: 260px;
   background: #f7f7f7;
   border-right: 1px solid #ddd;
   overflow-y: auto;
   flex-shrink: 0;
   transition: width 0.2s;
 }
 #sidebar.collapsed { width: 0; border: none; overflow: hidden; }
 #toc-container { padding: 8px; }
 .toc-item {
   padding: 6px 8px;
   cursor: pointer;
   font-size: 13px;
   border-radius: 4px;
   color: #333;
 }
 .toc-item:hover { background: #e0e0e0; }
 .toc-item.active { background: #d0d7ff; font-weight: 600; }

 #pdf-container {
   flex: 1;
   overflow: auto;
   display: flex;
   flex-direction: column;
   align-items: center;
   padding: 16px 0;
 }
 #pdf-container.flip-mode {
   justify-content: center;
   overflow: hidden;
 }
 .pdf-page {
   position: relative;
   margin-bottom: 8px;
   box-shadow: 0 2px 8px rgba(0,0,0,0.3);
   background: #fff;
 }
 .pdf-page canvas { display: block; }
 .pdf-page .textLayer {
   position: absolute;
   top: 0; left: 0; right: 0; bottom: 0;
   overflow: hidden;
   opacity: 0.2;
   line-height: 1.0;
 }
 .pdf-page .textLayer span {
   color: transparent;
   position: absolute;
   white-space: pre;
   cursor: text;
   transform-origin: 0% 0%;
 }
 .pdf-page .textLayer ::selection {
   background: rgba(0, 0, 255, 0.3);
 }

 #page-nav {
   display: none;
   justify-content: center;
   align-items: center;
   gap: 16px;
   padding: 8px;
   background: #323639;
   color: #fff;
   flex-shrink: 0;
 }
 #page-nav.visible { display: flex; }
 #page-nav button {
   background: #444;
   border: none;
   color: #fff;
   padding: 6px 16px;
   border-radius: 4px;
   cursor: pointer;
   font-size: 18px;
 }
 #page-nav button:hover { background: #555; }
 #page-input { width: 60px; text-align: center; padding: 4px; border-radius: 4px; border: 1px solid #555; background: #444; color: #fff; }

 #pdf-loading, #toc-loading {
   text-align: center;
   padding: 48px;
   color: #999;
 }

 .code-block-overlay {
   position: absolute;
   background: #f6f8fa;
   border: 1px solid #d1d5db;
   border-radius: 4px;
   padding: 8px;
   font-family: 'Consolas', 'Courier New', monospace;
   font-size: 12px;
   overflow: auto;
   white-space: pre;
 }
 ```

 ---

 ### Task 6: Core Viewer (viewer.js)

 **Files:**
 - Write: `js/viewer.js`

 **Interfaces:**
 - Consumes: `utils.js` — `getQueryParam()`, `getUrlHash()`, `updateUrlHash()`, `getBookConfig()`
 - Consumes: `toc.js` — `renderToc(pdf, container, onPageSelect)`
 - Consumes: `toolbar.js` — `initToolbar({onBack, onToggleToc, onToggleMode, onPageInput, title, currentPage, totalPages, mode})`
 - Produces: Loads PDF, manages scroll/flip modes, renders pages

 - [ ] **Step 1: Write `js/viewer.js`**

 ```javascript
 import { getQueryParam, getUrlHash, updateUrlHash, getBookConfig } from './utils.js';
 import { renderToc } from './toc.js';
 import { initToolbar } from './toolbar.js';

 // Configure PDF.js worker
 pdfjsLib.GlobalWorkerOptions.workerSrc = 'lib/pdfjs/pdf.worker.min.mjs';

 const container = document.getElementById('pdf-container');
 const loadingEl = document.getElementById('pdf-loading');
 const pageNav = document.getElementById('page-nav');

 let pdfDoc = null;
 let mode = 'scroll'; // 'scroll' | 'flip'
 let currentPage = 1;
 let totalPages = 0;
 let scale = 1.2;
 let renderedPages = new Map();

 // --- Mode switching ---

 function setMode(newMode) {
   mode = newMode;
   container.className = mode === 'flip' ? 'flip-mode' : '';
   pageNav.classList.toggle('visible', mode === 'flip');
   updateUrlHash({ mode });
   // Clear and re-render
   container.innerHTML = '';
   renderedPages.clear();
   if (mode === 'scroll') renderAllPages();
   else renderCurrentPage();
 }

 // --- PDF loading ---

 async function loadPDF(url) {
   loadingEl.style.display = 'block';
   try {
     const loadingTask = pdfjsLib.getDocument(url);
     pdfDoc = await loadingTask.promise;
     totalPages = pdfDoc.numPages;

     const outline = await pdfDoc.getOutline();
     renderToc(pdfDoc, document.getElementById('toc-container'), (pageNum) => {
       goToPage(pageNum);
     });

     const hash = getUrlHash();
     if (hash.mode) mode = hash.mode;
     currentPage = parseInt(hash.page) || 1;

     container.className = mode === 'flip' ? 'flip-mode' : '';
     pageNav.classList.toggle('visible', mode === 'flip');
     loadingEl.style.display = 'none';

     if (mode === 'scroll') renderAllPages();
     else renderCurrentPage();

   } catch (e) {
     loadingEl.textContent = '无法打开此书：' + e.message;
   }
 }

 // --- Scroll mode ---

 async function renderAllPages() {
   container.innerHTML = '';
   renderedPages.clear();
   for (let i = 1; i <= totalPages; i++) {
     // Create placeholder first, then render on demand
     const placeholder = document.createElement('div');
     placeholder.className = 'pdf-page';
     placeholder.id = `page-${i}`;
     placeholder.style.minHeight = '200px';
     container.appendChild(placeholder);
   }
   // Lazy render visible pages
   setupLazyRender();
   // Initial render of first few pages
   renderVisiblePages();

   if (currentPage > 1) {
     setTimeout(() => {
       document.getElementById(`page-${currentPage}`)?.scrollIntoView();
     }, 500);
   }
 }

 async function renderPage(pageNum) {
   if (renderedPages.has(pageNum)) return renderedPages.get(pageNum);
   const page = await pdfDoc.getPage(pageNum);
   const viewport = page.getViewport({ scale });

   const wrapper = document.getElementById(`page-${pageNum}`);
   if (!wrapper) return;

   const canvas = document.createElement('canvas');
   const ctx = canvas.getContext('2d');
   canvas.width = viewport.width;
   canvas.height = viewport.height;
   canvas.style.display = 'block';

   // Text layer
   const textLayerDiv = document.createElement('div');
   textLayerDiv.className = 'textLayer';
   textLayerDiv.style.width = viewport.width + 'px';
   textLayerDiv.style.height = viewport.height + 'px';

   wrapper.style.width = viewport.width + 'px';
   wrapper.style.height = viewport.height + 'px';

   wrapper.innerHTML = '';
   wrapper.appendChild(canvas);
   wrapper.appendChild(textLayerDiv);

   await page.render({ canvasContext: ctx, viewport }).promise;

   // Render text layer
   const textContent = await page.getTextContent();
   pdfjsLib.renderTextLayer({
     textContentSource: textContent,
     container: textLayerDiv,
     viewport,
     textDivs: [],
   });

   renderedPages.set(pageNum, wrapper);
   return wrapper;
 }

 function setupLazyRender() {
   const observer = new IntersectionObserver((entries) => {
     for (const entry of entries) {
       if (entry.isIntersecting) {
         const pageNum = parseInt(entry.target.id.split('-')[1]);
         renderPage(pageNum);
         // Update current page for TOC highlighting
         updateCurrentPageFromScroll();
       }
     }
   }, { root: container, rootMargin: '200px' });

   document.querySelectorAll('.pdf-page').forEach(el => observer.observe(el));
 }

 function renderVisiblePages() {
   const rect = container.getBoundingClientRect();
   const visibleTop = container.scrollTop - 200;
   const visibleBottom = visibleTop + rect.height + 400;

   for (const el of container.querySelectorAll('.pdf-page')) {
     const top = el.offsetTop;
     if (top >= visibleTop && top <= visibleBottom) {
       const pageNum = parseInt(el.id.split('-')[1]);
       renderPage(pageNum);
     }
   }
 }

 let scrollTimer;
 container.addEventListener('scroll', () => {
   if (mode !== 'scroll') return;
   clearTimeout(scrollTimer);
   scrollTimer = setTimeout(updateCurrentPageFromScroll, 100);
 });

 function updateCurrentPageFromScroll() {
   const rect = container.getBoundingClientRect();
   const centerY = rect.top + rect.height / 2;
   let bestPage = 1;
   let bestDist = Infinity;
   for (const [num, el] of renderedPages) {
     const pageRect = el.getBoundingClientRect();
     const dist = Math.abs(pageRect.top + pageRect.height/2 - centerY);
     if (dist < bestDist) { bestDist = dist; bestPage = num; }
   }
   currentPage = bestPage;
   updatePageIndicator();
   updateUrlHash({ page: currentPage });
 }

 // --- Flip mode ---

 async function renderCurrentPage() {
   container.innerHTML = '';
   renderedPages.clear();

   const page = await pdfDoc.getPage(currentPage);
   const viewport = page.getViewport({ scale: 1.5 });

   const wrapper = document.createElement('div');
   wrapper.className = 'pdf-page';

   const canvas = document.createElement('canvas');
   const ctx = canvas.getContext('2d');
   canvas.width = viewport.width;
   canvas.height = viewport.height;

   const textLayerDiv = document.createElement('div');
   textLayerDiv.className = 'textLayer';
   textLayerDiv.style.width = viewport.width + 'px';
   textLayerDiv.style.height = viewport.height + 'px';

   wrapper.style.width = viewport.width + 'px';
   wrapper.style.height = viewport.height + 'px';
   wrapper.appendChild(canvas);
   wrapper.appendChild(textLayerDiv);
   container.appendChild(wrapper);

   await page.render({ canvasContext: ctx, viewport }).promise;

   const textContent = await page.getTextContent();
   pdfjsLib.renderTextLayer({
     textContentSource: textContent,
     container: textLayerDiv,
     viewport,
     textDivs: [],
   });

   renderedPages.set(currentPage, wrapper);
   updatePageIndicator();
   updateUrlHash({ page: currentPage });
 }

 function goToPage(pageNum) {
   pageNum = Math.max(1, Math.min(pageNum, totalPages));
   currentPage = pageNum;
   document.getElementById('page-input').value = currentPage;
   if (mode === 'flip') {
     renderCurrentPage();
   } else {
     const target = document.getElementById(`page-${currentPage}`);
     target?.scrollIntoView({ behavior: 'smooth' });
   }
 }

 function nextPage() { goToPage(currentPage + 1); }
 function prevPage() { goToPage(currentPage - 1); }

 function updatePageIndicator() {
   document.getElementById('page-indicator').textContent = `${currentPage} / ${totalPages}`;
   document.getElementById('page-input').value = currentPage;
   document.getElementById('page-input').max = totalPages;
 }

 // --- Keyboard ---

 document.addEventListener('keydown', (e) => {
   if (mode === 'flip') {
     if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); nextPage(); }
     if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); prevPage(); }
   }
 });

 // --- Init ---

 async function init() {
   const bookId = getQueryParam('book');
   if (!bookId) {
     loadingEl.textContent = '未指定书籍';
     return;
   }

   const book = await getBookConfig(bookId);
   if (!book) {
     loadingEl.textContent = '未找到书籍配置';
     return;
   }

   document.getElementById('book-title').textContent = book.title;
   document.title = book.title;

   initToolbar({
     onBack: () => { window.location.href = 'index.html'; },
     onToggleToc: () => {
       document.getElementById('sidebar').classList.toggle('collapsed');
     },
     onToggleMode: () => {
       setMode(mode === 'scroll' ? 'flip' : 'scroll');
     },
     onPageInput: (n) => { goToPage(n); },
     title: book.title,
     getCurrentPage: () => currentPage,
     getTotalPages: () => totalPages,
     getMode: () => mode,
   });

   await loadPDF(book.file);
 }

 init();
 ```

 ---

 ### Task 7: TOC and Toolbar

 **Files:**
 - Write: `js/toc.js`
 - Write: `js/toolbar.js`

 **Interfaces:**
 - `renderToc(pdf, container, onPageSelect)` — renders outline tree into `container`, calls `onPageSelect(pageNum)` on click.
 - `initToolbar({onBack, onToggleToc, onToggleMode, onPageInput, title, getCurrentPage, getTotalPages, getMode})` — wires up toolbar buttons.

 - [ ] **Step 1: Write `js/toc.js`**

 ```javascript
 export async function renderToc(pdf, container, onPageSelect) {
   container.innerHTML = '';
   let outline;
   try {
     outline = await pdf.getOutline();
   } catch (e) {
     outline = null;
   }

   if (!outline || outline.length === 0) {
     // Fallback: just list page numbers
     const total = pdf.numPages;
     for (let i = 1; i <= total; i++) {
       const item = createPageItem(i, onPageSelect);
       container.appendChild(item);
     }
     return;
   }

   function renderItems(items, depth = 0) {
     for (const item of items) {
       const div = document.createElement('div');
       div.className = 'toc-item';
       div.style.paddingLeft = (8 + depth * 16) + 'px';
       div.textContent = item.title;
       div.addEventListener('click', async () => {
         let pageNum;
         try {
           if (item.dest) {
             const dest = typeof item.dest === 'string'
               ? await pdf.getDestination(item.dest)
               : item.dest;
             pageNum = await pdf.getPageIndex(dest[0]) + 1;
           }
         } catch (e) {}
         if (pageNum) onPageSelect(pageNum);

         // Highlight active
         container.querySelectorAll('.toc-item').forEach(el => el.classList.remove('active'));
         div.classList.add('active');
       });
       container.appendChild(div);
       if (item.items && item.items.length > 0) {
         renderItems(item.items, depth + 1);
       }
     }
   }

   renderItems(outline);
 }

 function createPageItem(n, onPageSelect) {
   const div = document.createElement('div');
   div.className = 'toc-item';
   div.textContent = `第 ${n} 页`;
   div.addEventListener('click', () => onPageSelect(n));
   return div;
 }
 ```

 - [ ] **Step 2: Write `js/toolbar.js`**

 ```javascript
 export function initToolbar(opts) {
   document.getElementById('btn-back').addEventListener('click', opts.onBack);
   document.getElementById('btn-toc').addEventListener('click', opts.onToggleToc);
   document.getElementById('btn-mode').addEventListener('click', () => {
     opts.onToggleMode();
     updateModeButton(opts.getMode());
   });

   document.getElementById('btn-prev').addEventListener('click', () => {
     opts.onPageInput(opts.getCurrentPage() - 1);
   });
   document.getElementById('btn-next').addEventListener('click', () => {
     opts.onPageInput(opts.getCurrentPage() + 1);
   });

   const pageInput = document.getElementById('page-input');
   pageInput.addEventListener('keydown', (e) => {
     if (e.key === 'Enter') {
       const n = parseInt(pageInput.value);
       if (n >= 1 && n <= opts.getTotalPages()) {
         opts.onPageInput(n);
       }
     }
   });

   updateModeButton(opts.getMode());
 }

 function updateModeButton(mode) {
   const btn = document.getElementById('btn-mode');
   btn.innerHTML = mode === 'scroll' ? '&#9776;' : '&#9776;';
   btn.title = mode === 'scroll' ? '切换到翻页模式' : '切换到滚动模式';
   // Use different unicode icons
   btn.innerHTML = mode === 'scroll' ? '&#9638;' : '&#9776;';
   btn.title = mode === 'scroll' ? '翻页模式' : '滚动模式';
 }
 ```

 ---

 ### Task 8: Code Highlighting Integration

 **Files:**
 - Modify: `js/viewer.js` (add code detection after text layer render)

 - [ ] **Step 1: Add code highlighting after page render in `viewer.js`**

 After the text layer is rendered in both `renderPage()` and `renderCurrentPage()`, add a call to detect code blocks. Insert after `pdfjsLib.renderTextLayer(...)`:

 ```javascript
 // Detect and highlight code blocks
 detectCodeBlocks(textLayerDiv, viewport);
 ```

 Define the detection function in `viewer.js`:

 ```javascript
 function detectCodeBlocks(textLayer, viewport) {
   const spans = Array.from(textLayer.querySelectorAll('span'));
   if (spans.length === 0) return;

   // Group spans by approximate lines (Y coordinate clusters)
   const lines = [];
   let currentLine = [];
   let lastY = null;
   const Y_THRESHOLD = 2;

   for (const span of spans) {
     const y = parseFloat(span.style.top) || 0;
     if (lastY === null || Math.abs(y - lastY) < Y_THRESHOLD) {
       currentLine.push(span);
     } else {
       if (currentLine.length > 0) lines.push(currentLine);
       currentLine = [span];
     }
     lastY = y;
   }
   if (currentLine.length > 0) lines.push(currentLine);

   // Detect code: consecutive lines starting with 2+ spaces or tab
   const codeKeywords = /\b(int|void|char|float|double|if|for|while|return|class|struct|public|private|static|const|#include|using|namespace|def|import|print|function|var|let|const)\b/;
   let codeBlockStart = -1;
   let codeLines = [];

   for (let i = 0; i < lines.length; i++) {
     const lineText = lines[i].map(s => s.textContent).join('');
     const isCodeLine = /^[\s]{2,}\S/.test(lineText) || codeKeywords.test(lineText.trim());

     if (isCodeLine) {
       if (codeBlockStart === -1) codeBlockStart = i;
       codeLines.push(lines[i]);
     } else {
       if (codeLines.length >= 3) {
         highlightBlock(codeLines, viewport);
       }
       codeBlockStart = -1;
       codeLines = [];
     }
   }
   if (codeLines.length >= 3) highlightBlock(codeLines, viewport);
 }

 function highlightBlock(codeLines, viewport) {
   if (codeLines.length === 0) return;

   // Compute bounding box
   const firstSpan = codeLines[0][0];
   const lastLine = codeLines[codeLines.length - 1];
   const lastSpan = lastLine[lastLine.length - 1];

   const top = parseFloat(firstSpan.style.top) - 2;
   const left = 0;
   const right = Math.max(...codeLines.flatMap(line => {
     const s = line[line.length - 1];
     return parseFloat(s.style.left) + parseFloat(s.style.width || '0');
   }));
   const bottom = parseFloat(lastSpan.style.top) + parseFloat(lastSpan.style.height || '14') + 2;

   const overlay = document.createElement('div');
   overlay.className = 'code-block-overlay';
   overlay.style.left = left + 'px';
   overlay.style.top = top + 'px';
   overlay.style.width = (right + 16) + 'px';
   overlay.style.height = (bottom - top) + 'px';

   const codeText = codeLines.map(line => line.map(s => s.textContent).join('')).join('\n');
   overlay.textContent = codeText;

   if (typeof hljs !== 'undefined') {
     const result = hljs.highlightAuto(codeText);
     overlay.innerHTML = `<code class="hljs language-${result.language || 'plaintext'}">${result.value}</code>`;
   }

   codeLines[0][0].closest('.pdf-page').appendChild(overlay);
 }
 ```

 - [ ] **Step 2: Add highlight.js script tag to `viewer.html`**

 ```html
 <script src="lib/highlight.min.js"></script>
 ```

 Add before the `module` script tag for viewer.js.

 ---

 ### Task 9: Integration, Polish, and Verification

 **Files:**
 - Modify: `js/toolbar.js` — fix mode button icon
 - Modify: `js/bookshelf.js` — fix PDF path references
 - Modify: `js/viewer.js` — fix pdfjsLib import, add error handling for file://

 - [ ] **Step 1: Add PDF.js script tag to `viewer.html` and `index.html`**

 In both `index.html` and `viewer.html`, before the module script:

 ```html
 <script src="lib/pdfjs/pdf.min.mjs" type="module"></script>
 ```

 Actually, since PDF.js is ESM, import it in viewer.js and bookshelf.js:

 In `viewer.js` top:
 ```javascript
 import * as pdfjsLib from '../lib/pdfjs/pdf.min.mjs';
 ```

 In `bookshelf.js` top:
 ```javascript
 import * as pdfjsLib from '../lib/pdfjs/pdf.min.mjs';
 ```

 - [ ] **Step 2: Configure PDF.js worker path in both files**

 ```javascript
 pdfjsLib.GlobalWorkerOptions.workerSrc = '../lib/pdfjs/pdf.worker.min.mjs';
 ```

 - [ ] **Step 3: Handle file:// protocol — disable range requests**

 In both viewer.js and bookshelf.js, before `getDocument()`:

 ```javascript
 if (window.location.protocol === 'file:') {
   pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('../lib/pdfjs/pdf.worker.min.mjs', import.meta.url).href;
 }
 ```

 - [ ] **Step 4: Fix mode button icon properly**

 In `js/toolbar.js`, update `updateModeButton`:

 ```javascript
 function updateModeButton(mode) {
   const btn = document.getElementById('btn-mode');
   if (mode === 'scroll') {
     btn.innerHTML = '&#x1F4C4;';
     btn.title = '切换到翻页模式';
   } else {
     btn.innerHTML = '&#x1F4D6;';
     btn.title = '切换到滚动模式';
   }
 }
 ```

 - [ ] **Step 5: Update books.json paths to be relative from index.html location**

 The PDFs are at the workspace root `F:\大一下文件\算法书\*.pdf`. Since index.html is also at root, paths should be relative. Update books.json:

 Change each file path to relative from root, e.g.:
 `"file": "大话数据结构 (程杰) (z-library.sk, 1lib.sk, z-lib.sk).pdf"`

 - [ ] **Step 6: Full verification**

 1. Open `F:\大一下文件\算法书\index.html` in Chrome/Edge
 2. Verify bookshelf shows 4 books with covers
 3. Click a book — verify viewer opens with PDF rendered
 4. Verify text is selectable (try dragging to select)
 5. Toggle flip mode — verify single page with navigation arrows
 6. Toggle back to scroll mode — verify continuous scroll
 7. Verify TOC panel opens/closes
 8. Verify code blocks get syntax highlighting (check 大话数据结构 for code examples)

 - [ ] **Step 7: Commit**

 ```bash
 git add -A
 git commit -m "feat: complete PDF book reader v1"
 ```
