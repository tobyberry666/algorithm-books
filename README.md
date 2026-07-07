# 📚 算法书 — 把 PDF 教材变成「可滚动、可复制」的自包含网页

> 一行命令，把任意 PDF（文字版 / 扫描版）转成不依赖任何外部资源的 HTML 阅读页；
> 同时内置一个纯静态书架 + PDF.js 阅读器，可就地翻看原版 PDF。

**核心卖点**：`git clone` 下来 → 把自己想看的 PDF 丢进目录 → 一条命令 → 得到一个
**可滚动、可选中复制、双击即开**的自包含 HTML（`converted/<书名>/index.html`），
不引用仓库任何 `lib/`，可以直接丢到任意静态服务器或 GitHub Pages。

---

## ✨ 两种阅读方式

| 方式 | 命令 / 入口 | 适合 | 复制文字 |
|------|------------|------|----------|
| **A. 转换后的 HTML** | `python converter/convert.py 你的书.pdf` | 长期阅读、想复制片段 | ✅ 文字版天然可复制；扫描版装了 tesseract 后也可复制 |
| **B. PDF.js 原版阅读器** | 打开 `index.html` → 点「PDF 版」 | 想看原版排版、公式 | ✅ 文字层透明化，可选中 |
| **图书画廊** | 打开 `index.html` | 书架挑书 | — |

> 两种方式都纯静态、零后端、零 CDN。

---

## 🚀 快速开始

### 1. 装依赖

```bash
pip install -r requirements.txt
```

- `pymupdf`：**必装**，PDF 解析与渲染（提供 `fitz`）。
- `pillow` + `pytesseract`：**OCR 用**，扫描版要可复制文字才需要。
- 仓库自带 `pypkgs/fitz` 作为兜底；装了上面的就走 pip 版，二选一即可。

### 2. 转换任意一本 PDF → 自包含 HTML

```bash
# 最常用：转换单个 PDF（自动判断「文字版 / 扫描版」）
python converter/convert.py 我的书.pdf

# 指定输出目录与书名
python converter/convert.py 我的书.pdf -o ./out/我的书 --title "我的书"

# 扫描版想可复制？先装好 tesseract（见下方「OCR 说明」），再开 OCR
python converter/convert.py 扫描书.pdf --ocr --lang chi_sim+eng
```

转换完会生成：

```
converted/我的书/
├── index.html        # 自包含：CSS/JS 内联，代码高亮所需的 hljs 也复制进来了
├── images/           # 每页图片（扫描版）或配图（文字版）
└── assets/           # highlight.min.*（仅文字版有）
```

用浏览器打开 `converted/我的书/index.html` 即可阅读（建议走 http 服务器，
`file://` 下个别浏览器会限制某些资源加载）。

### 3. 用书架画廊（PDF.js 阅读器）

```bash
python -m http.server 3000
# 浏览器打开 http://localhost:3000/index.html
```

> ⚠️ 必须用 HTTP 服务器启动，`file://` 协议会被 CORS 阻止。

---

## 🔤 OCR 说明（扫描版可复制文字的关键）

扫描版 PDF 没有内嵌文字，默认转出来是「每页一张高清图」，**文字不可选中复制**。
想要可复制，需要 OCR：

1. **系统装 tesseract 二进制** 并加入 `PATH`：
   - Windows：装 [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) 安装包，勾选中文包 `chi_sim`。
   - macOS：`brew install tesseract tesseract-lang`
   - Linux：`sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
2. 装 Python 依赖：`pip install pytesseract pillow`（已在 `requirements.txt`）。
3. 重新转换：`python converter/convert.py 扫描书.pdf --ocr`。

转换后的扫描页会叠一层**与图片对齐、透明但可选中**的 OCR 文字层（`.ocr-layer`），
于是扫描书也能像文字书一样 Ctrl+C 复制。

> 本机没装 tesseract？没关系，转换器会**优雅降级为纯图片**，并在页面顶部提示如何开启 OCR。

---

## 📂 项目结构

```
算法书/
├── index.html              # [画廊] 书架入口
├── viewer.html             # [Phase 1] PDF.js 阅读器
├── books.json              # 书籍配置（书架 + 转换器批量用）
├── converter/
│   └── convert.py          # [Phase 2] PDF → 自包含 HTML 转换器（纯 CLI）
├── requirements.txt        # pip 依赖清单
├── lib/                    # 书架/阅读器用的 pdfjs + highlight.js（转换器不依赖它）
├── css/  js/               # 书架与阅读器样式/逻辑
├── pypkgs/                 # PyMuPDF 兜底（gitignore，建议用 pip 装）
└── converted/              # 转换输出（gitignore；只部署 poster 作为最小 demo）
    └── poster/             # 文字版示范（已部署到 GitHub Pages）
```

---

## 📖 已收录书籍

| 书名 | 类型 | PDF 版 | HTML 版 |
|------|------|--------|---------|
| Poster | 文字型（1 页） | ✅ | ✅ 已部署（最小 demo） |
| 大话数据结构 | 扫描版 | ✅ | 本地转换后可用 |
| 深入浅出程序设计竞赛（基础篇） | 扫描版 | ✅ | 本地转换后可用 |
| 算法竞赛（上册） | 扫描版 | ✅ | 本地转换后可用 |
| 算法竞赛（下册） | 扫描版 | ✅ | 本地转换后可用 |

> `converted/` 被 gitignore：**clone 后默认只有 poster demo 在线可见**，其余书
> 请本地跑 `python converter/convert.py --batch` 一键生成（保留书架画廊）。

---

## 🛠 技术栈

- **PDF 渲染**：PDF.js 3.11（零 CDN，本地内置）
- **代码高亮**：highlight.js 11.9
- **PDF 转换**：PyMuPDF 1.28（转换器核心）
- **纯静态**：无后端、无框架、无构建工具

---

## 📋 路线图

- [x] **Phase 1**：静态书架 + PDF.js 阅读器（滚动/翻页/目录/代码高亮）
- [x] **Phase 2**：CLI 转换器产品化（可移植、自包含、OCR 可选）
- [ ] **Phase 3**：在线服务（Web 上传 → 转换 → 在线阅读 / 下载 zip）— 见 `server/`

详见 [PROGRESS.md](./PROGRESS.md) 与 [handoff.md](./handoff.md)。

---

## 📄 许可

MIT License
