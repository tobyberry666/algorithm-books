# 算法书 — 项目进度与总结

> 最后更新：2026-07-07 | 三阶段路线（Phase 1 ✅ / Phase 2 ✅ / Phase 3 🟡）

---

## 一、三阶段路线总览

| 阶段 | 目标 | 状态 |
|------|------|------|
| **Phase 1** | 纯静态 PDF 阅读器：书架 + PDF.js 阅读器 + 目录导航 | ✅ 完成 |
| **Phase 2** | CLI 转换器：PDF → 自包含 HTML 阅读文件夹 | ✅ 产品化完成 |
| **Phase 3** | 在线服务：Web 上传 → 转换 → 在线阅读 | 🟡 脚手架已建（`server/`） |

```
F:\大一下文件\算法书\
├── index.html                  ← [Phase 1] 书架入口
├── viewer.html                 ← [Phase 1] PDF.js 阅读器
├── books.json                  ← [Phase 1/2] 书籍配置（书架 + 批量转换共用）
├── css/  js/                   ← [Phase 1] 书架 + 阅读器样式与逻辑
├── lib/
│   ├── pdfjs/                  ← [Phase 1] PDF.js 3.11（本地内置）
│   └── highlight.min.*         ← [Phase 1] highlight.js 11.9（本地内置）
├── converter/
│   └── convert.py              ← [Phase 2] PDF→HTML 转换器（纯 CLI，可移植）
├── requirements.txt            ← [Phase 2] pip 依赖清单
├── server/
│   └── web_app.py              ← [Phase 3] Web 上传转换服务（脚手架）
├── converted/                  ← [Phase 2] 转换输出（gitignore；仅 poster 部署为 demo）
│   ├── poster/                 ← 文字型 PDF 示范（已部署到 GitHub Pages）
│   ├── dahua-datastructure/
│   ├── shen-ru-qian-chu/
│   ├── algorithm-contest-1/
│   └── algorithm-contest-2/    ← 扫描版（本地生成；含 images/）
└── *.pdf                       ← 5 本原始 PDF（4 扫描 + 1 文字）
```

---

## 二、Phase 1：PDF.js 阅读器（已完成）

### 2.1 书架页（index.html）

- 封面自动从 PDF 首页截取缩略图（localStorage 缓存）
- 每本书两个按钮：蓝色 **PDF 版**（PDF.js 阅读器）、黄色 **HTML 版**（转换后的页面）
- HTML 版按钮只在 `books.json` 中配置了 `converted` 字段时显示
- 5 本书：Poster（文字型）、大话数据结构、深入浅出程序设计竞赛（基础篇）、算法竞赛（上册）、算法竞赛（下册）

### 2.2 PDF.js 阅读器（viewer.html）

| 功能 | 说明 |
|------|------|
| 滚动模式 | 全文连续垂直滚动，IntersectionObserver 懒渲染 |
| 翻页模式 | 单页居中，自适应 viewport，键盘 ← → 翻页，点击左右半区翻页 |
| 目录导航 | 从 PDF outline 提取章节树，点击跳转；无 outline 回退到页码列表 |
| URL hash | 刷新页面恢复页码和阅读模式 |
| 代码高亮 | 启发式检测代码块，hljs.highlightAuto 着色 |
| 渲染精度 | 根据 window.devicePixelRatio 自动适配（上限 2.5x），高分屏不模糊 |
| **文字层透明化** | 文字层 `color: transparent`，**既能选中复制、又不再双影**（见下） |

### 2.3 修复过的问题

- **textLayer 重影（已彻底解决）**：早期注释掉 `renderTextLayer` 只保留 canvas → 文字不可选。
  现改为 `.textLayer span { color: transparent }`（`css/viewer.css`）+ 恢复 `renderTextLayer`
  （`js/viewer.js`）：**文字层可见但透明，无重影、可复制**。
- **渲染模糊**：默认 scale 1.2 → 改为 Min(devicePixelRatio, 2.5)，高分屏自动 2x 渲染
- **书架 card 无按钮**：原整张卡片只支持点击 → 改为两个独立按钮（PDF 版 / HTML 版）

---

## 三、Phase 2：转换器（已产品化）

`converter/convert.py` 使用 PyMuPDF 将任意 PDF 转为静态、自包含 HTML：

- **纯 CLI、可移植**：不再写死项目路径，任何人 clone 后放任意 PDF 即可转。
- **自动识别文字版 / 扫描版**（`detect_mode`）：
  - 文字版：抽结构化文本（标题/段落/代码块/配图），天然可选中复制
  - 扫描版：每页渲染高清图；装了 tesseract 时 `--ocr` 叠加透明但可选中的 OCR 文字层
- **输出完全自包含**：CSS/JS 内联，hljs 复制到 `assets/`，**不引用 `../../lib`**
- 无 tesseract 时扫描版优雅降级为纯图片，并在页面顶部给提示

用法：

```bash
python converter/convert.py 我的书.pdf            # 单本
python converter/convert.py --batch               # 读 books.json 批量重转
python converter/convert.py 扫描书.pdf --ocr      # 扫描版开 OCR（需 tesseract）
```

依赖管理：**不再依赖仓库内的 `pypkgs/` 兜底路径**，统一 `pip install -r requirements.txt`
（`pymupdf` 必装；`pillow`+`pytesseract` 用于 OCR）。`pypkgs/` 仅作为极端兜底保留，已 gitignore。

### 转换实测

| 书籍 | 类型 | 模式 | 结果 |
|------|------|------|------|
| poster | 文字型 | text | ✅ 5KB 纯文本 + hljs，自包含 |
| 算法竞赛（下册） | 扫描版 | scan | ✅ 330 张图，本机无 tesseract 退化为纯图片 |
| 大话数据结构 / 深入浅出 / 算法竞赛（上册） | 扫描版 | scan | ✅ 本地生成，dpi 110 |

---

## 四、当前书架状态

| 书名 | 类型 | PDF 版 | HTML 版（converted 字段） |
|------|------|--------|------|
| Poster | 文字型（1 页） | 正常 | ✅ `converted/poster/index.html`（已部署） |
| 大话数据结构 | 扫描版（463 页） | 正常 | ✅ 本地已生成 |
| 深入浅出程序设计竞赛（基础篇） | 扫描版（327 页） | 正常 | ✅ 本地已生成 |
| 算法竞赛（上册） | 扫描版（406 页） | 正常 | ✅ 本地已生成 |
| 算法竞赛（下册） | 扫描版（330 页） | 正常 | ✅ `converted/algorithm-contest-2/index.html` |

> `converted/` 被 gitignore，clone 后默认只有 poster demo 在线可见；
> 其余书请本地 `python converter/convert.py --batch` 一键生成。

---

## 五、Phase 3：Web 上传服务（脚手架）

`server/web_app.py`：上传 PDF → 后台调用 `converter/convert.py` → 返回在线阅读链接 / 下载 zip。
当前为最小可用版（标准库 `http.server`，无第三方依赖），详见文件内注释与 README。

---

## 六、部署（GitHub Pages）

- `master` 推送触发 `.github/workflows/deploy.yml` → `peaceiris/actions-gh-pages` 推到 `gh-pages`
  （`build_type=legacy`，同域避免 CORS）。
- **PDF 通过 Git LFS 管理**并随站点部署，PDF.js 阅读器同域可读，无跨域问题。
- `converted/` 被 deploy 排除（避免扫描版全本图片撑爆 Pages）；仅 `converted/poster`
  被 force-add 进仓库作为最小 demo 部署。
- ⚠️ **容量注意**：单本扫描版全转 HTML 可能数十 MB（下册 330 张图），不适合整体部署；
  文档化「本地转换本地看」。

---

## 七、测试方式

```bash
# 启动服务器
cd F:\大一下文件\算法书
python -m http.server 3000
# 浏览器打开 http://localhost:3000/index.html
```

**注意**：必须用 HTTP 服务器，`file://` 协议会被 CORS 阻止 ES modules 和 fetch()。

---

## 八、技术决策记录

| 决策 | 原因 |
|------|------|
| PDF.js 而非原生渲染 | 保留原书排版（公式、图表零损失），避免转换失真 |
| `<script>` 加载 PDF.js 而非 ES module | npm 输出是 UMD 格式（.js），不是 ES module |
| 所有依赖本地内置 | 沙箱和 in-app 浏览器均无法访问 CDN |
| PyMuPDF 做转换器 | 轻量、快，文字/扫描双模式都支持 |
| 扫描版图片存外部文件 | inline base64 导致 HTML 过大，浏览器卡死 |
| **文字层透明化（非禁用）** | 高分屏 canvas 与文字层错位 → 透明化既去重影又保留复制能力 |
| DPI 自适应渲染 | 固定 1.2x 在高分屏模糊，devicePixelRatio 自适应 |
| `converted/` gitignore + 仅部署 poster | 扫描版全本图片过大，Pages 容量受限 |
| pip 依赖代替 pypkgs 兜底 | 可移植性：clone 后 `pip install -r requirements.txt` 即用 |
