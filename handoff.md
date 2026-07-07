# 算法书 — 项目交接文档

> 最后更新：2026-07-07 | 目标读者：接手此项目的开发者
> 跨会话记忆与「下一步」以 [`NEXT_STEPS.md`](./NEXT_STEPS.md) 为准，本文档聚焦当前架构与踩坑。

## 一、项目目标

把中文 PDF 算法教材转成两种可读形态，后续发展为面向公众的开源项目：

1. **PDF.js 原版阅读器**（书架画廊，在线翻看原版 PDF）
2. **自包含 HTML**（转换器产出，可滚动、可复制，双击即开，可独立部署）

**三阶段路线：**

1. **Phase 1（完成）**：核心阅读器 — 纯静态 HTML + PDF.js，书架 + 阅读器
2. **Phase 2（完成）**：CLI 转换器 — 输入 PDF → 输出自包含阅读文件夹
3. **Phase 3（脚手架）**：在线服务 — Web 上传 → 转换 → 在线阅读（`server/web_app.py`）

---

## 二、项目结构（当前真实状态）

```
F:\大一下文件\算法书\
├── index.html                  ← [OK] 书架入口
├── viewer.html                 ← [OK] PDF.js 阅读器
├── books.json                  ← [OK] 书籍配置（书架 + 转换器批量共用）
├── css/  js/                   ← [OK] 书架 + 阅读器样式与逻辑
├── lib/
│   ├── pdfjs/                  ← [OK] PDF.js 3.11.174（本地内置，零 CDN）
│   └── highlight.min.*         ← [OK] highlight.js 11.9（本地内置）
├── converter/
│   └── convert.py              ← [OK] PDF→HTML 转换器（纯 CLI，可移植）
├── requirements.txt            ← [OK] pip 依赖清单（pymupdf 必装；pillow/pytesseract OCR 用）
├── server/
│   └── web_app.py              ← [Phase 3] Web 上传转换服务脚手架
├── converted/                  ← [生成物] 转换 HTML（gitignore；仅 poster 部署为 demo）
│   ├── poster/  dahua-datastructure/  shen-ru-qian-chu/
│   ├── algorithm-contest-1/  algorithm-contest-2/
└── *.pdf                       ← 5 本原始 PDF（4 扫描 + 1 文字，Git LFS 管理）
```

> ⚠️ `pypkgs/` 仍存在但**仅作兜底**（gitignore）。转换器优先用 `pip install -r requirements.txt`
> 装的 PyMuPDF；仅在 import 不到时才回退到 `pypkgs/fitz`。不要再把 pypkgs 当主依赖写进文档。

---

## 三、当前状态：已完成

### 1. PDF.js 阅读器（Phase 1）

- 书架页：5 本书封面卡片，从 PDF 首页自动截缩略图（localStorage 缓存）
- 滚动模式（默认）/ 翻页模式（← → 翻页，点左右半区翻页）
- 目录导航（PDF outline → 章节树），无 outline 回退页码列表
- **文字层透明化**：`css/viewer.css` 中 `.textLayer span { color: transparent }` + `js/viewer.js`
  恢复 `renderTextLayer` → **文字可选中复制，且无双影**（早期「禁用 textLayer」方案已废弃）
- 代码高亮：`hljs.highlightAuto` 启发式着色
- URL hash 状态保持

### 2. 转换器（Phase 2，产品化完成）

`converter/convert.py` 已重写为纯 CLI：

- 不写死任何路径，clone 后放任意 PDF 即可转
- 自动识别「文字版 / 扫描版」
- 文字版抽结构化文本（标题/段落/代码块/配图），天然可复制
- 扫描版每页渲染高清图；装 tesseract 后 `--ocr` 叠加透明可选中的 OCR 文字层
- 输出自包含（CSS/JS 内联，hljs 复制到 `assets/`，不引用 `../../lib`）

运行方式：

```bash
pip install -r requirements.txt          # 装依赖（不再用 PYTHONPATH=pypkgs）
python converter/convert.py 我的书.pdf    # 单本
python converter/convert.py --batch       # 读 books.json 批量重转（保留画廊）
python converter/convert.py 扫描书.pdf --ocr   # 扫描版开 OCR（需系统装 tesseract）
```

### 3. 关于 auto-fix 标注

转换器对自动检测内容加视觉标记：`[自动识别代码块]` / `[自动识别标题]`（黄色左边框）。
**当前限制**：4 本算法书全是扫描版、无内嵌文字，所以 auto-fix 在实际书页中**不会出现**——
标签只在**文字型 PDF**正文生效。`poster` 这本文字型 PDF 已验证机制正常。

---

## 四、已知问题 & 注意事项

1. **`file://` 协议不支持**：ES modules 和 `fetch()` 在 `file://` 下被 CORS 阻止。必须用 HTTP 服务器。
2. **OCR 依赖系统 tesseract 二进制**：`pytesseract` 只是 Python 封装，本机还需装 tesseract +
   中文包 `chi_sim`。未装时扫描版优雅降级为纯图片（页面顶部有提示）。
3. **`converted/` 不进仓库**：clone 后默认只有 `poster` demo；其余书本地 `python converter/convert.py --batch` 生成。
4. **容量**：扫描版全本转 HTML 可能数十 MB，不适合整体部署到 GitHub Pages；已文档化「本地转换本地看」，仅部署 poster 作示范。
5. **Git LFS + Pages**：PDF 走 LFS；部署用 `peaceiris/actions-gh-pages` + `build_type=legacy`，同域避免 CORS（详见 `DEPLOY-LOG.md`）。

---

## 五、关键技术决策

| 决策 | 原因 |
|------|------|
| PDF.js 而非原生渲染 | 保留原书排版（公式、图表零损失） |
| 本地内置所有依赖 | 沙箱和 in-app 浏览器均无法访问 CDN |
| PyMuPDF 做转换器 | 轻量、快，文字/扫描双模式都支持 |
| 单页 HTML（全本书一页）+ 侧边栏锚点 | 书架跳转 = 页内锚点，labuladong 风格 |
| **文字层透明化（非禁用）** | 去重影 + 保留复制能力 |
| pip 依赖代替 pypkgs 兜底 | clone 后 `pip install -r requirements.txt` 即用，可移植 |
| `converted/` gitignore + 仅部署 poster | 扫描版全本图片过大，Pages 容量受限 |

---

## 六、接手指引

1. 读 [`NEXT_STEPS.md`](./NEXT_STEPS.md) —— 含跨会话记忆 + 下一阶段任务（A→E）。
2. 本地起服务：`python -m http.server 3000` → `http://localhost:3000/index.html`。
3. 想新增一本：把 PDF 丢进目录 → 在 `books.json` 加条目 → `python converter/convert.py --batch`。
4. `DEPLOY-LOG.md` 记录了 GitHub Pages 部署的全部踩坑，改部署流程前必读。
