 import { getQueryParam, getUrlHash, updateUrlHash, getBookConfig } from './utils.js';
 import { renderToc } from './toc.js';
 import { initToolbar } from './toolbar.js';
 
 // pdfjsLib loaded via <script> in HTML — config worker path
 pdfjsLib.GlobalWorkerOptions.workerSrc = 'lib/pdfjs/pdf.worker.min.js';
 
 const container = document.getElementById('pdf-container');
 const loadingEl = document.getElementById('pdf-loading');
 const pageNav = document.getElementById('page-nav');
 const sidebar = document.getElementById('sidebar');
 
 let pdfDoc = null;
 let mode = 'scroll';
 let currentPage = 1;
 let totalPages = 0;
 const scale = Math.min(window.devicePixelRatio || 1, 2.5);
 const renderedPages = new Map();
 
 // --- Mode ---
 function setMode(newMode) {
   mode = newMode;
   container.className = mode === 'flip' ? 'flip-mode' : '';
   pageNav.classList.toggle('visible', mode === 'flip');
   updateUrlHash({ mode });
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
 
     const tocContainer = document.getElementById('toc-container');
     try {
       const outline = await pdfDoc.getOutline();
       renderToc(pdfDoc, outline, tocContainer, goToPage);
     } catch (e) {
       renderToc(pdfDoc, null, tocContainer, goToPage);
     }
 
     const hash = getUrlHash();
     if (hash.mode) mode = hash.mode;
     currentPage = parseInt(hash.page) || 1;
 
     container.className = mode === 'flip' ? 'flip-mode' : '';
     pageNav.classList.toggle('visible', mode === 'flip');
     loadingEl.style.display = 'none';
 
     if (mode === 'scroll') renderAllPages();
     else renderCurrentPage();
     updatePageIndicator();
 
   } catch (e) {
     loadingEl.textContent = '无法打开此书：' + e.message;
   }
 }
 
 // --- Scroll mode ---
 async function renderAllPages() {
   container.innerHTML = '';
   renderedPages.clear();
   for (let i = 1; i <= totalPages; i++) {
     const ph = document.createElement('div');
     ph.className = 'pdf-page';
     ph.id = 'page-' + i;
     ph.style.minHeight = '800px';
     ph.style.width = '800px';
     container.appendChild(ph);
   }
   setupLazyRender();
   renderVisiblePages();
   if (currentPage > 1) {
     setTimeout(() => {
       document.getElementById('page-' + currentPage)?.scrollIntoView();
     }, 300);
   }
 }
 
 async function renderPage(pageNum) {
   if (renderedPages.has(pageNum)) return renderedPages.get(pageNum);
   const page = await pdfDoc.getPage(pageNum);
   const viewport = page.getViewport({ scale });
   const wrapper = document.getElementById('page-' + pageNum);
   if (!wrapper) return null;
 
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
   wrapper.innerHTML = '';
   wrapper.appendChild(canvas);
   wrapper.appendChild(textLayerDiv);
 
   await page.render({ canvasContext: ctx, viewport }).promise;
 
//    const textContent = await page.getTextContent();
//    pdfjsLib.renderTextLayer({
//      textContentSource: textContent,
//      container: textLayerDiv,
//      viewport,
//      textDivs: [],
//    });
 
   renderedPages.set(pageNum, wrapper);
   // Code highlighting
   detectCodeBlocks(textLayerDiv);
   return wrapper;
 }
 
 function setupLazyRender() {
   const observer = new IntersectionObserver((entries) => {
     for (const entry of entries) {
       if (entry.isIntersecting) {
         const pageNum = parseInt(entry.target.id.split('-')[1]);
         if (!isNaN(pageNum)) renderPage(pageNum);
       }
     }
   }, { root: container, rootMargin: '400px' });
   container.querySelectorAll('.pdf-page').forEach(el => observer.observe(el));
 }
 
 function renderVisiblePages() {
   const rect = container.getBoundingClientRect();
   const vs = container.scrollTop - 300;
   const ve = vs + rect.height + 600;
   for (const el of container.querySelectorAll('.pdf-page')) {
     const t = el.offsetTop;
     if (t >= vs && t <= ve) {
       const pageNum = parseInt(el.id.split('-')[1]);
       if (!isNaN(pageNum)) renderPage(pageNum);
     }
   }
 }
 
 let scrollTimer;
 container.addEventListener('scroll', () => {
   if (mode !== 'scroll') return;
   clearTimeout(scrollTimer);
   scrollTimer = setTimeout(() => {
     updateCurrentPageFromScroll();
     renderVisiblePages();
   }, 150);
 });
 
 function updateCurrentPageFromScroll() {
   const rect = container.getBoundingClientRect();
   const cy = rect.top + rect.height * 0.3;
   let best = 1;
   let bestDist = Infinity;
   for (const [num, el] of renderedPages) {
     const pr = el.getBoundingClientRect();
     const d = Math.abs(pr.top + pr.height * 0.3 - cy);
     if (d < bestDist) { bestDist = d; best = num; }
   }
   if (best !== currentPage) {
     currentPage = best;
     updatePageIndicator();
     updateUrlHash({ page: currentPage });
   }
 }
 
 // --- Flip mode ---
 async function renderCurrentPage() {
   container.innerHTML = '';
   renderedPages.clear();
   const page = await pdfDoc.getPage(currentPage);
   // Fit page to viewport
   const containerHeight = container.clientHeight - 32;
   const containerWidth = container.clientWidth - 32;
   const origView = page.getViewport({ scale: 1 });
   const scaleH = containerHeight / origView.height;
   const scaleW = containerWidth / origView.width;
   const fitScale = Math.min(scaleH, scaleW, 2.5);
   const viewport = page.getViewport({ scale: fitScale });
 
   const wrapper = document.createElement('div');
   wrapper.className = 'pdf-page';
   wrapper.style.width = viewport.width + 'px';
   wrapper.style.height = viewport.height + 'px';
 
   const canvas = document.createElement('canvas');
   const ctx = canvas.getContext('2d');
   canvas.width = viewport.width;
   canvas.height = viewport.height;
 
   const textLayerDiv = document.createElement('div');
   textLayerDiv.className = 'textLayer';
   textLayerDiv.style.width = viewport.width + 'px';
   textLayerDiv.style.height = viewport.height + 'px';
 
   wrapper.appendChild(canvas);
   wrapper.appendChild(textLayerDiv);
   container.appendChild(wrapper);
 
   await page.render({ canvasContext: ctx, viewport }).promise;
//    const textContent = await page.getTextContent();
//    pdfjsLib.renderTextLayer({
//      textContentSource: textContent,
//      container: textLayerDiv,
//      viewport,
//      textDivs: [],
//    });
 
   renderedPages.set(currentPage, wrapper);
   detectCodeBlocks(textLayerDiv);
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
     const target = document.getElementById('page-' + currentPage);
     if (target) {
       target.scrollIntoView({ behavior: 'smooth' });
     }
   }
 }
 
 function updatePageIndicator() {
   document.getElementById('page-indicator').textContent = currentPage + ' / ' + totalPages;
   document.getElementById('page-input').value = currentPage;
   document.getElementById('page-input').max = totalPages;
 }
 
 // --- Code highlighting ---
 function detectCodeBlocks(textLayer) {
   if (typeof hljs === 'undefined') return;
   const spans = Array.from(textLayer.querySelectorAll('span'));
   if (spans.length === 0) return;
 
   const lines = [];
   let currentLine = [];
   let lastY = null;
   const Y_THRESHOLD = 3;
 
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
 
   const codeKeywords = /\b(int|void|char|float|double|if|for|while|return|class|struct|public|private|static|const|#include|using|namespace|def|import|print|function|var|let|const|scanf|printf|cout|cin|endl|main|bool|long|short|unsigned|signed|auto|break|continue|else|switch|case|default|do|goto|register|sizeof|typedef|union|enum|extern|volatile|template|typename|virtual|override|new|delete|this|try|catch|throw)\b/i;
   let codeLines = [];
 
   for (let i = 0; i < lines.length; i++) {
     const lineText = lines[i].map(s => s.textContent).join('');
     const isCodeLine = /^[\s]{2,}\S/.test(lineText) || codeKeywords.test(lineText.trim());
 
     if (isCodeLine) {
       codeLines.push(lines[i]);
     } else {
       if (codeLines.length >= 3) addCodeOverlay(codeLines);
       codeLines = [];
     }
   }
   if (codeLines.length >= 3) addCodeOverlay(codeLines);
 }
 
 function addCodeOverlay(codeLines) {
   if (codeLines.length === 0) return;
   const firstSpan = codeLines[0][0];
   const lastLine = codeLines[codeLines.length - 1];
   const lastSpan = lastLine[lastLine.length - 1];
   if (!lastSpan) return;
 
   const firstLefts = codeLines[0].map(s => parseFloat(s.style.left) || 0);
   const left = Math.min(...firstLefts);
   const maxRights = codeLines.map(line => {
     const s = line[line.length - 1];
     return (parseFloat(s.style.left) || 0) + (parseFloat(s.style.width) || 0);
   });
   const right = Math.max(...maxRights);
   const top = parseFloat(firstSpan.style.top) - 2;
   const bottom = parseFloat(lastSpan.style.top) + parseFloat(lastSpan.style.height || '14') + 2;
 
   const overlay = document.createElement('div');
   overlay.className = 'code-block-overlay';
   overlay.style.left = left + 'px';
   overlay.style.top = top + 'px';
   overlay.style.width = (right - left + 16) + 'px';
   overlay.style.height = (bottom - top) + 'px';
 
   const codeText = codeLines.map(line => line.map(s => s.textContent).join('')).join('\n');
   const result = hljs.highlightAuto(codeText);
   overlay.innerHTML = '<code class="hljs language-' + (result.language || 'plaintext') + '">' + result.value + '</code>';
 
   firstSpan.closest('.pdf-page').appendChild(overlay);
 }
 
 // --- Keyboard ---
 document.addEventListener('keydown', (e) => {
   if (e.target.tagName === 'INPUT') return;
   if (mode === 'flip') {
     if (e.key === 'ArrowRight' || e.key === 'ArrowDown') { e.preventDefault(); goToPage(currentPage + 1); }
     if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') { e.preventDefault(); goToPage(currentPage - 1); }
   }
 });
 
 // --- Click page halves (flip mode) ---
 container.addEventListener('click', (e) => {
   if (mode !== 'flip') return;
   if (e.target.closest('.code-block-overlay') || e.target.closest('.textLayer')) return;
   const rect = container.getBoundingClientRect();
   const midX = rect.left + rect.width / 2;
   if (e.clientX < midX) goToPage(currentPage - 1);
   else goToPage(currentPage + 1);
 });
 
 // --- Init ---
 async function init() {
   const bookId = getQueryParam('book');
   if (!bookId) { loadingEl.textContent = '未指定书籍'; return; }
   const book = await getBookConfig(bookId);
   if (!book) { loadingEl.textContent = '未找到书籍配置'; return; }
 
   document.getElementById('book-title').textContent = book.title;
   document.title = book.title;
 
   initToolbar({
     onBack: () => { window.location.href = 'index.html'; },
     onToggleToc: () => { sidebar.classList.toggle('collapsed'); },
     onToggleMode: () => { setMode(mode === 'scroll' ? 'flip' : 'scroll'); },
     onPageInput: (n) => { goToPage(n); },
     getCurrentPage: () => currentPage,
     getTotalPages: () => totalPages,
     getMode: () => mode,
   });
 
   await loadPDF(book.file);
 }
 
 init();
