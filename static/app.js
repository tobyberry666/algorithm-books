/* PDF 批注工坊 —— 前端逻辑（同时服务于在线版与导出的独立 HTML） */
(function () {
  "use strict";

  const EMBEDDED = window.__EMBEDDED__ || null;
  const STANDALONE = !!EMBEDDED;
  if (STANDALONE) document.body.classList.add("standalone");

  const $ = (s) => document.querySelector(s);
  const homeEl = $("#home"), viewerEl = $("#viewer"), pagesEl = $("#pages"),
    annListEl = $("#ann-list"), selBar = $("#sel-bar"),
    zoomEl = $("#zoom"), zoomVal = $("#zoom-val"),
    docTitle = $("#doc-title"), annCount = $("#ann-count");

  const state = {
    doc: null, annotations: [], zoom: 1.2, docId: null,
    rendered: new Set(), tool: "highlight",
  };

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }
  function escapeAttr(s) { return (s || "").replace(/"/g, "&quot;"); }
  function clsOf(type) { return type === "underline" ? "ul" : type === "note" ? "note" : ""; }

  let io = null; // IntersectionObserver 实例（须早于启动块，避免 TDZ）

  /* ---------------------- 启动 ---------------------- */
  if (STANDALONE) {
    state.doc = EMBEDDED.doc;
    state.docId = state.doc.id;
    const saved = (() => { try { return localStorage.getItem("anno-" + state.docId); } catch (e) { return null; } })();
    state.annotations = saved ? JSON.parse(saved) : (EMBEDDED.annotations || []);
    openViewer();
  } else {
    const docId = new URLSearchParams(location.search).get("doc");
    if (docId) loadDoc(docId);
    else showHome();
  }

  /* ---------------------- 首页 ---------------------- */
  function showHome() {
    homeEl.classList.remove("hidden");
    viewerEl.classList.add("hidden");
    loadDocs();
  }

  async function loadDocs() {
    try {
      const docs = await (await fetch("/api/docs")).json();
      const grid = $("#docs");
      grid.innerHTML = "";
      $("#docs-empty").classList.toggle("hidden", docs.length > 0);
      docs.forEach((d) => {
        const card = document.createElement("div");
        card.className = "doc-card";
        card.innerHTML =
          `<div class="t">${escapeHtml(d.title)}</div>
           <div class="m">${d.page_count} 页 · ${escapeHtml(d.filename)}</div>
           <div class="row">
             <a class="open" href="?doc=${d.id}">打开</a>
             <button class="del">删除</button>
           </div>`;
        card.querySelector(".del").onclick = async () => {
          if (!confirm("删除该文档及其批注？")) return;
          await fetch("/api/doc/" + d.id, { method: "DELETE" });
          loadDocs();
        };
        grid.appendChild(card);
      });
    } catch (e) { console.error(e); }
  }

  if (!STANDALONE) {
    const drop = $("#drop"), fileInput = $("#file");
    fileInput.addEventListener("change", (e) => { if (e.target.files[0]) uploadFile(e.target.files[0]); });
    ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("drag"); }));
    ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("drag"); }));
    drop.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) uploadFile(f); });

    async function uploadFile(file) {
      const buf = await file.arrayBuffer();
      const r = await fetch("/api/upload", {
        method: "POST",
        headers: { "Content-Type": "application/octet-stream", "X-Filename": encodeURIComponent(file.name) },
        body: buf,
      });
      const j = await r.json();
      if (j.error) { alert(j.error); return; }
      location.href = "?doc=" + j.id;
    }
  }

  async function loadDoc(id) {
    state.docId = id;
    const [d, a] = await Promise.all([
      fetch("/api/doc/" + id).then((r) => r.json()),
      fetch("/api/annotations/" + id).then((r) => r.json()),
    ]);
    state.doc = d;
    state.annotations = a || [];
    openViewer();
  }

  /* ---------------------- 阅读视图 ---------------------- */

  function openViewer() {
    if (homeEl) homeEl.classList.add("hidden");
    viewerEl.classList.remove("hidden");
    docTitle.textContent = state.doc.title || state.doc.filename || "文档";
    zoomEl.value = state.zoom;
    zoomVal.textContent = state.zoom.toFixed(1) + "x";
    buildPages();
    renderSidebar();
  }

  function buildPages() {
    if (io) { io.disconnect(); io = null; }
    pagesEl.innerHTML = "";
    state.rendered.clear();
    const z = state.zoom;
    state.doc.pages.forEach((pg, i) => {
      const wrap = document.createElement("div");
      wrap.className = "page-wrap";
      wrap.dataset.page = i;
      wrap.style.width = pg.w * z + "px";
      wrap.style.height = pg.h * z + "px";
      const page = document.createElement("div");
      page.className = "page";
      page.dataset.page = i;
      page.style.width = pg.w * z + "px";
      page.style.height = pg.h * z + "px";
      wrap.appendChild(page);
      pagesEl.appendChild(wrap);
      observePage(wrap, z);
    });
  }

  function observePage(wrap, z) {
    if (!io) {
      io = new IntersectionObserver((entries) => {
        entries.forEach((en) => {
          if (!en.isIntersecting) return;
          const wrap = en.target;
          const i = +wrap.dataset.page;
          const page = wrap.querySelector(".page");
          if (!state.rendered.has(i)) {
            renderPage(page, state.doc.pages[i], z);
            state.rendered.add(i);
          }
        });
      }, { root: pagesEl, rootMargin: "700px 0px" });
    }
    io.observe(wrap);
  }

  function renderPage(page, pg, z) {
    const parts = [];
    if (pg.image_page) parts.push(`<img class="page-bg" src="${pg.image_page}">`);
    (pg.imgs || []).forEach((im) => {
      if (!im.src) return;
      parts.push(`<img src="${im.src}" style="position:absolute;left:${im.x * z}px;top:${im.y * z}px;width:${im.w * z}px;height:${im.h * z}px;">`);
    });
    (pg.spans || []).forEach((s, si) => {
      const style =
        `left:${s.x * z}px;top:${s.y * z}px;font-size:${s.size * z}px;` +
        `font-family:${escapeAttr(s.font)},sans-serif;color:${s.color};` +
        `font-weight:${s.weight};font-style:${s.style}`;
      parts.push(`<span class="ts" data-si="${si}" style="${style}">${escapeHtml(s.t)}</span>`);
    });
    page.innerHTML = parts.join("");
    applyAnnotationsToPage(page, +page.dataset.page);
  }

  /* ---------------------- 选区 → 标注范围 ---------------------- */
  function closestTs(node) {
    if (!node) return null;
    if (node.nodeType === 3) node = node.parentElement;
    return node ? node.closest(".ts") : null;
  }
  function offsetWithinTs(tsEl, node, offset) {
    if (node && node.nodeType !== 3 && node.firstChild) { node = node.firstChild; offset = 0; }
    let total = 0;
    const walker = document.createTreeWalker(tsEl, NodeFilter.SHOW_TEXT, null);
    let n;
    while ((n = walker.nextNode())) {
      if (n === node) return total + offset;
      total += n.textContent.length;
    }
    return offset;
  }

  function getSelectionInfo() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return null;
    const range = sel.getRangeAt(0);
    if (range.collapsed) return null;
    const startEl = closestTs(range.startContainer);
    const endEl = closestTs(range.endContainer);
    if (!startEl || !endEl) return null;
    const pageEl = startEl.closest(".page");
    if (!pageEl || pageEl !== endEl.closest(".page")) return null;
    const pageNo = +pageEl.dataset.page;
    const spans = [...pageEl.querySelectorAll(".ts")];
    const sIdx = spans.indexOf(startEl), eIdx = spans.indexOf(endEl);
    if (sIdx < 0 || eIdx < 0) return null;
    const ranges = [];
    spans.forEach((el, idx) => {
      const si = +el.dataset.si;
      const text = el.textContent;
      if (idx < sIdx || idx > eIdx) return;
      if (idx === sIdx && idx === eIdx)
        ranges.push({ si, page: pageNo, start: offsetWithinTs(el, range.startContainer, range.startOffset), end: offsetWithinTs(el, range.endContainer, range.endOffset) });
      else if (idx === sIdx)
        ranges.push({ si, page: pageNo, start: offsetWithinTs(el, range.startContainer, range.startOffset), end: text.length });
      else if (idx === eIdx)
        ranges.push({ si, page: pageNo, start: 0, end: offsetWithinTs(el, range.endContainer, range.endOffset) });
      else
        ranges.push({ si, page: pageNo, start: 0, end: text.length });
    });
    const clean = ranges.filter((r) => r.end > r.start);
    if (!clean.length) return null;
    return { page: pageNo, ranges: clean, text: sel.toString() };
  }

  /* ---------------------- 选区浮动条 ---------------------- */
  let lastSel = null;
  document.addEventListener("mouseup", (e) => {
    if (e.target.closest("#sel-bar")) return;
    setTimeout(() => {
      const info = getSelectionInfo();
      if (info) { lastSel = info; showSelBar(info); }
      else hideSelBar();
    }, 10);
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { hideSelBar(); window.getSelection().removeAllRanges(); } });
  pagesEl.addEventListener("scroll", hideSelBar, true);

  function showSelBar() {
    const rect = window.getSelection().getRangeAt(0).getBoundingClientRect();
    selBar.classList.remove("hidden");
    selBar.style.left = Math.min(rect.left, window.innerWidth - 230) + "px";
    selBar.style.top = rect.bottom + 6 + "px";
  }
  function hideSelBar() { selBar.classList.add("hidden"); }

  selBar.querySelectorAll("button").forEach((b) => {
    b.addEventListener("click", () => {
      const act = b.dataset.act;
      if (act === "cancel") { hideSelBar(); window.getSelection().removeAllRanges(); return; }
      if (lastSel) createAnnotation(act, lastSel);
      hideSelBar();
    });
  });

  /* ---------------------- 标注 CRUD ---------------------- */
  function createAnnotation(type, info) {
    const id = "a" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    state.annotations.push({
      id, type, text: info.text, note: "", ranges: info.ranges,
      page: info.page, created: Date.now(),
    });
    const pageEl = pagesEl.querySelector(`.page[data-page="${info.page}"]`);
    if (pageEl) applyAnnotationsToPage(pageEl, info.page);
    renderSidebar();
    saveAnnotations();
    if (type === "note") focusNote(id);
    window.getSelection().removeAllRanges();
  }

  function deleteAnnotation(id) {
    state.annotations = state.annotations.filter((a) => a.id !== id);
    pagesEl.querySelectorAll(".page").forEach((p) => applyAnnotationsToPage(p, +p.dataset.page));
    renderSidebar();
    saveAnnotations();
  }

  function applyAnnotationsToPage(pageEl, pageNo) {
    const bySi = {};
    state.annotations.forEach((a) => {
      (a.ranges || []).forEach((r) => {
        if (r.page !== pageNo) return;
        (bySi[r.si] = bySi[r.si] || []).push({ start: r.start, end: r.end, id: a.id, type: a.type });
      });
    });
    pageEl.querySelectorAll(".ts").forEach((el) => {
      const si = +el.dataset.si;
      const ranges = bySi[si];
      const text = el.textContent;
      if (!ranges || !ranges.length) { el.textContent = text; return; }
      const owner = new Array(text.length).fill(null);
      ranges.forEach((r) => {
        for (let i = Math.max(0, r.start); i < Math.min(text.length, r.end); i++) owner[i] = { id: r.id, type: r.type };
      });
      let html = "", i = 0;
      while (i < text.length) {
        const o = owner[i];
        let j = i;
        while (j < text.length && sameOwner(owner[j], o)) j++;
        const seg = escapeHtml(text.slice(i, j));
        html += o ? `<mark class="anno ${clsOf(o.type)}" data-anno-id="${o.id}">${seg}</mark>` : seg;
        i = j;
      }
      el.innerHTML = html;
    });
  }
  function sameOwner(a, b) { if (a === b) return true; if (!a || !b) return false; return a.id === b.id && a.type === b.type; }

  /* ---------------------- 侧栏 ---------------------- */
  function renderSidebar() {
    annCount.textContent = state.annotations.length;
    annListEl.innerHTML = "";
    state.annotations.forEach((a) => {
      const card = document.createElement("div");
      card.className = "ann " + (a.type === "underline" ? "ul" : a.type === "note" ? "note" : "");
      card.dataset.id = a.id;
      const label = a.type === "underline" ? "下划线" : a.type === "note" ? "批注" : "高亮";
      card.innerHTML =
        `<div class="quote">${escapeHtml(a.text || "").slice(0, 140)}</div>
         <textarea placeholder="写点批注…">${escapeHtml(a.note || "")}</textarea>
         <div class="row"><span class="muted">${label}</span><button class="del">删除</button></div>`;
      card.addEventListener("click", (e) => {
        if (e.target.tagName !== "TEXTAREA" && !e.target.classList.contains("del")) jumpTo(a.id);
      });
      card.querySelector("textarea").addEventListener("input", (e) => { a.note = e.target.value; saveAnnotations(); });
      card.querySelector(".del").addEventListener("click", (e) => { e.stopPropagation(); deleteAnnotation(a.id); });
      annListEl.appendChild(card);
    });
  }

  function focusNote(id) {
    const card = annListEl.querySelector(`.ann[data-id="${id}"]`);
    if (card) { card.scrollIntoView({ block: "nearest" }); card.querySelector("textarea").focus(); }
  }

  function jumpTo(id) {
    document.querySelectorAll("mark.anno.active").forEach((m) => m.classList.remove("active"));
    document.querySelectorAll(".ann.active").forEach((c) => c.classList.remove("active"));
    const a = state.annotations.find((x) => x.id === id);
    if (a) {
      const pageEl = pagesEl.querySelector(`.page[data-page="${a.page}"]`);
      if (pageEl && !state.rendered.has(a.page)) { renderPage(pageEl, state.doc.pages[a.page], state.zoom); state.rendered.add(a.page); }
      const mark = pagesEl.querySelector(`mark.anno[data-anno-id="${id}"]`);
      if (mark) { mark.scrollIntoView({ behavior: "smooth", block: "center" }); mark.classList.add("active"); }
    }
    const card = annListEl.querySelector(`.ann[data-id="${id}"]`);
    if (card) card.classList.add("active");
  }

  pagesEl.addEventListener("click", (e) => {
    const m = e.target.closest("mark.anno");
    if (m) jumpTo(m.dataset.annoId);
  });

  /* ---------------------- 保存 ---------------------- */
  let saveTimer = null;
  function saveAnnotations() {
    if (STANDALONE) {
      try { localStorage.setItem("anno-" + state.docId, JSON.stringify(state.annotations)); } catch (e) {}
      return;
    }
    clearTimeout(saveTimer);
    saveTimer = setTimeout(async () => {
      try {
        await fetch("/api/annotations/" + state.docId, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify(state.annotations),
        });
      } catch (e) { console.error(e); }
    }, 400);
  }

  /* ---------------------- 工具栏 ---------------------- */
  zoomEl.addEventListener("input", () => {
    state.zoom = parseFloat(zoomEl.value);
    zoomVal.textContent = state.zoom.toFixed(1) + "x";
    buildPages();
  });
  const btnExport = $("#btn-export");
  if (btnExport) btnExport.addEventListener("click", () => { if (STANDALONE) return; saveAnnotations(); window.location = "/api/export/" + state.docId; });
  const btnBack = $("#btn-back");
  if (btnBack) btnBack.addEventListener("click", () => { if (STANDALONE) return; location.href = "/"; });
})();
