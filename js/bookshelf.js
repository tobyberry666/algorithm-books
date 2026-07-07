 import { getAllBooks, getThumbnail, saveThumbnail } from './utils.js';
 
 // pdfjsLib loaded via <script> in HTML — config worker path
 pdfjsLib.GlobalWorkerOptions.workerSrc = 'lib/pdfjs/pdf.worker.min.js';
 
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
     console.warn('Cover generation failed for', book.title, e);
     return null;
   }
 }
 
 function createBookCard(book, coverUrl) {
   const card = document.createElement('div');
   card.className = 'book-card';
 
   const cover = document.createElement('div');
   cover.className = coverUrl ? 'book-cover' : 'book-cover no-image';
   if (coverUrl) {
     const img = document.createElement('img');
     img.src = coverUrl;
     img.style.width = '100%';
     img.style.height = '100%';
     img.style.objectFit = 'cover';
     img.alt = book.title;
     cover.appendChild(img);
   } else {
     cover.textContent = book.title;
   }
 
   const info = document.createElement('div');
   info.className = 'book-info';
   info.innerHTML =
     '<div class="title">' + book.title + '</div>' +
     '<div class="author">' + (book.author || '') + '</div>';
 
   card.appendChild(cover);
   card.appendChild(info);
 
   // Action buttons
   const actions = document.createElement('div');
   actions.className = 'book-actions';

   const pdfBtn = document.createElement('button');
   pdfBtn.className = 'btn-pdf';
   pdfBtn.textContent = 'PDF 版';
   pdfBtn.addEventListener('click', (e) => {
     e.stopPropagation();
     window.location.href = 'viewer.html?book=' + encodeURIComponent(book.id);
   });
   actions.appendChild(pdfBtn);

  // 仅 poster 提供在线 HTML 版；其余书为扫描版，本地转换后才可用，画廊不展示该按钮
  if (book.converted && book.id === 'poster') {
    const htmlBtn = document.createElement('button');
    htmlBtn.className = 'btn-html';
    htmlBtn.textContent = 'HTML 版';
    htmlBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      window.location.href = book.converted;
    });
    actions.appendChild(htmlBtn);
  }

   card.appendChild(actions);
 
   return card;
 }
 
 async function init() {
   try {
     const books = await getAllBooks();
     shelf.innerHTML = '';
     for (const book of books) {
       // Show card immediately (no cover yet) for fast paint
       const card = createBookCard(book, null);
       shelf.appendChild(card);
       // Generate cover async and update
       generateCover(book).then(coverUrl => {
         if (coverUrl) {
           const cover = card.querySelector('.book-cover');
           if (cover) {
             cover.classList.remove('no-image');
             const img = document.createElement('img');
             img.src = coverUrl;
             img.style.width = '100%';
             img.style.height = '100%';
             img.style.objectFit = 'cover';
             img.alt = book.title;
             cover.innerHTML = '';
             cover.appendChild(img);
           }
         }
       });
     }
   } catch (e) {
     shelf.innerHTML = '<div class="loading">加载失败，请检查 books.json 配置</div>';
     console.error(e);
   }
 }
 
 init();
