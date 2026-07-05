# PDF Book Reader — 项目进度与总结

> 编写日期：2026-07-05 | 三阶段路线

---

## 一、三阶段路线总览

| 阶段 | 目标 | 状态 |
|------|------|------|
| **Phase 1** | 纯静态 PDF 阅读器：书架 + PDF.js 阅读器 + 目录导航 | ✅ 基本完成 |
| **Phase 2** | CLI 转换器：PDF → 自包含 HTML 阅读文件夹 | 🟡 核心可用，待产品化 |
| **Phase 3** | 在线服务：Web 上传 → 转换 → 在线阅读 | ⬜ 未开始 |

`
F:\大一下文件\算法书\
├── index.html                  ← [Phase 1] 书架入口
├── viewer.html                 ← [Phase 1] 阅读器页面
├── books.json                  ← [Phase 1] 书籍配置
├── css/
│   ├── bookshelf.css           ← [Phase 1] 书架样式
│   └── viewer.css              ← [Phase 1] 阅读器样式
├── js/
│   ├── utils.js                ← [Phase 1] 工具函数
│   ├── bookshelf.js            ← [Phase 1] 书架逻辑（双按钮：PDF 版 / HTML 版）
│   ├── viewer.js               ← [Phase 1] PDF.js 阅读器（滚动/翻页/代码高亮）
│   ├── toc.js                  ← [Phase 1] 目录导航
│   └── toolbar.js              ← [Phase 1] 工具栏交互
├── lib/
│   ├── pdfjs/                  ← [Phase 1] PDF.js 3.11.174（本地内置）
│   └── highlight.min.*         ← [Phase 1] highlight.js 11.9.0（本地内置）
├── converter/
│   └── convert.py              ← [Phase 2] PDF→HTML 转换器（PyMuPDF）
├── pypkgs/
│   └── fitz/                   ← PyMuPDF 1.28.0（本地安装）
├── converted/                  ← [Phase 2] 转换输出目录
│   ├── poster/
│   │   ├── index.html          ← 5KB 纯文本（文字型 PDF 示范）
│   │   └── images/
│   └── algorithm-contest-2/
│       ├── index.html          ← 69KB + 330 张外部 PNG
│       └── images/
└── *.pdf                       ← 5 本原始 PDF（4 扫描 + 1 文字）
`

---

## 二、Phase 1：已完成的工作

### 2.1 书架页（index.html）

- 封面自动从 PDF 首页截取缩略图（localStorage 缓存）
- 每本书两个按钮：蓝色 **PDF 版**（PDF.js 阅读器）、黄色 **HTML 版**（转换后的页面）
- HTML 版按钮只在 ooks.json 中配置了 converted 字段时显示
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

### 2.3 修复过的问题

- **textLayer 重影**：用户看到两遍文字（canvas 层 + textLayer 层未对齐）→ 注释掉 renderTextLayer 调用，只保留 canvas 渲染
- **渲染模糊**：默认 scale 只有 1.2 → 改为 Min(devicePixelRatio, 2.5)，高分屏自动 2x 渲染
- **书架 card 无按钮**：原来整张卡片只支持点击 → 改为两个独立按钮（PDF 版 / HTML 版）

---

## 三、Phase 2：转换器

### 3.1 功能

converter/convert.py 使用 PyMuPDF 将 PDF 转为静态 HTML 页面：

- 使用方式：
  `
  python converter/convert.py --book <book-id>    # 单本
  python converter/convert.py                     # 全部
  `
- 输出结构：converted/<book-id>/index.html + images/ 文件夹
- 文字型 PDF：提取文本段落，代码块自动识别标注（auto-fix 类 + [自动识别代码块] 标签），标题自动检测
- 扫描版 PDF：每页导出为 PNG 图片（懒加载），左侧保留章节导航侧边栏
- 图片全部存为独立文件，HTML 保持在 100KB 以内，加载秒开

### 3.2 犯过的错与教训

| # | 问题 | 原因 | 修复 |
|---|------|------|------|
| 1 | convert.py 无法运行 | Out-File 写入时引入了前导空格 + BOM 字符 + 重复 import sys | 用 Python 逐行清理，utf-8-sig 去 BOM |
| 2 | ModuleNotFoundError: No module named 'fitz' | sys.path.insert 放在 import fitz 之后，顺序反了 | 把 sys.path.insert 移到文件顶部，在所有 import 之前 |
| 3 | HTML 版本右侧半边什么都没有 | 图片用 base64 内嵌，单个 HTML 文件 67MB，浏览器直接卡死 | 改为图片存外部文件，HTML 瘦身到 69KB |
| 4 | HTML 版 404 错误 | CSS/JS 引用路径 ../lib/ 少了一级，从 converted/book/ 向上需要 ../../lib/ | 路径改为 ../../lib/ |
| 5 | 反复 404 | Start-Process 的 --directory 参数被 Powershell 吞掉，服务器跑在错误目录 | 改用 Start-Job + Set-Location |
| 6 | apply_patch 频繁失败 | 文件有尾随空格、Unicode 字符、混合缩进（3空格/5空格） | 改用 Python 脚本直接读写文件 |

### 关于 auto-fix 标注

转换器对自动检测的内容加了视觉标记：
- 黄色背景 + 橙色左边框
- [自动识别代码块] / [自动识别标题] 标签
- Hover 时虚线外框

**当前限制**：4 本算法书全是扫描版，没有可提取的文字，所以 auto-fix 在实际书页中不会出现——标签只会在 **文字型 PDF** 的正文中生效。Poster 这本文字型 PDF 验证了机制是正常的。

---

## 四、当前书架状态

| 书名 | 类型 | PDF 版 | HTML 版 |
|------|------|--------|---------|
| Poster | 文字型（1页） | 正常 | 5KB 纯文本 |
| 大话数据结构 | 扫描版（463页） | 正常 | 待转换 |
| 深入浅出程序设计竞赛（基础篇） | 扫描版（327页） | 正常 | 待转换 |
| 算法竞赛（上册） | 扫描版（406页） | 正常 | 待转换 |
| 算法竞赛（下册） | 扫描版（330页） | 正常 | 69KB + 330张图片 |

---

## 五、接下来要做的

### Phase 1 收尾

转换剩余 3 本扫描版书籍（命令已就绪，每本约 30-45 秒）：

`
python converter/convert.py --book dahua-datastructure
python converter/convert.py --book shen-ru-qian-chu
python converter/convert.py --book algorithm-contest-1
`

跑完后在 books.json 里加 converted 字段即可。

### Phase 2 产品化

- 将 converter/convert.py 打磨为独立 CLI 工具
- 支持 pdf-to-html input.pdf --output ./my-book/
- 输出自包含文件夹（含 reader HTML + 转换内容），双击即用

### Phase 3（远期）

- Web UI：上传 PDF → 后台转换 → 在线阅读或下载 zip

---

## 六、测试方式

`
# 启动服务器
Set-Location "F:\大一下文件\算法书"
python -m http.server 3000

# 浏览器打开
http://localhost:3000/index.html
`

**注意**：必须用 HTTP 服务器，file:// 协议会被 CORS 阻止 ES modules 和 fetch()。

---

## 七、技术决策记录

| 决策 | 原因 |
|------|------|
| PDF.js 而非原生渲染 | 保留原书排版（公式、图表零损失），避免转换失真 |
| <script> 加载 PDF.js 而非 ES module | npm 输出是 UMD 格式（.js），不是 ES module |
| 所有依赖本地内置 | 沙箱和 in-app 浏览器均无法访问 CDN |
| PyMuPDF 而非 pdfplumber | pdfplumber pip 安装超时；PyMuPDF 更轻量更快 |
| 扫描版图片存外部文件 | inline base64 导致 HTML 过大，浏览器无法渲染 |
| 禁用 textLayer | 高分屏上 canvas 与文字层错位导致重影 |
| DPI 自适应渲染 | 固定 1.2x 在高分屏上模糊，devicePixelRatio 自适应 |
