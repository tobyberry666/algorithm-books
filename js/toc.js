 export async function renderToc(pdf, outline, container, onPageSelect) {
   container.innerHTML = '';
 
   if (!outline || outline.length === 0) {
     const total = pdf.numPages;
     for (let i = 1; i <= total; i++) {
       const div = document.createElement('div');
       div.className = 'toc-item';
       div.textContent = '第 ' + i + ' 页';
       div.addEventListener('click', () => onPageSelect(i));
       container.appendChild(div);
     }
     return;
   }
 
   function renderItems(items, depth) {
     depth = depth || 0;
     for (const item of items) {
       const div = document.createElement('div');
       div.className = 'toc-item level-' + Math.min(depth + 1, 3);
       div.textContent = item.title;
       div.addEventListener('click', async () => {
         let pageNum = null;
         try {
           if (item.dest) {
             const dest = typeof item.dest === 'string'
               ? await pdf.getDestination(item.dest)
               : item.dest;
             if (dest) pageNum = await pdf.getPageIndex(dest[0]) + 1;
           }
         } catch (e) { /* fall through */ }
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
