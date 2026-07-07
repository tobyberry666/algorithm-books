 // utils.js — Shared helpers for PDF Book Reader
 
 export function getQueryParam(name) {
   const params = new URLSearchParams(window.location.search);
   return params.get(name);
 }
 
 let _booksConfig = null;
 
 export async function loadBooksConfig() {
   if (_booksConfig) return _booksConfig;
   const resp = await fetch('books.json');
   _booksConfig = await resp.json();
   return _booksConfig;
 }
 
 export async function getBookConfig(bookId) {
   const config = await loadBooksConfig();
   return config.books.find(b => b.id === bookId) || null;
 }
 
 export async function getAllBooks() {
   const config = await loadBooksConfig();
   return config.books;
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
