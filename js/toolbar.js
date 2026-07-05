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
   if (mode === 'scroll') {
     btn.innerHTML = '&#9638; 翻页';
     btn.title = '切换到翻页模式';
   } else {
     btn.innerHTML = '&#9776; 滚动';
     btn.title = '切换到滚动模式';
   }
 }
