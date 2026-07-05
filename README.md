# 📚 算法书 — PDF Book Reader

> 把枯燥的算法 PDF 教材变成优雅的在线书架 + 交互式阅读器。

一个纯静态的 HTML/CSS/JS 书架系统，用 PDF.js 在浏览器里直接渲染 PDF，支持滚动阅读、翻页模式、目录导航和代码高亮。附带 PDF → HTML 转换器（PyMuPDF），可将扫描版/文字版 PDF 转为自包含的静态 HTML 页面。

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 📖 书架页 | 封面自动截取（PDF 首页缩略图），双按钮入口 |
| 📜 滚动模式 | 全文连续垂直滚动，懒渲染，大量页数不卡 |
| 📄 翻页模式 | 单页居中，键盘 ← → / 点击翻页 |
| 🗂 目录导航 | 从 PDF outline 提取章节树，点击跳转 |
| 🎨 代码高亮 | 启发式检测代码块，hljs 自动着色 |
| 🔗 URL 持久化 | 刷新页面恢复页码和阅读模式 |
| 🖥 高分屏适配 | devicePixelRatio 自适应渲染，不模糊 |

## 📂 项目结构

```
算法书/
├── index.html              # 书架入口
├── viewer.html             # PDF.js 阅读器
├── books.json              # 书籍配置
├── PROGRESS.md             # 项目进度与总结
├── handoff.md              # 交接文档
├── css/
│   ├── bookshelf.css       # 书架样式
│   └── viewer.css          # 阅读器样式
├── js/
│   ├── utils.js            # 工具函数
│   ├── bookshelf.js        # 书架逻辑
│   ├── viewer.js           # PDF.js 阅读器核心
│   ├── toc.js              # 目录导航
│   └── toolbar.js          # 工具栏交互
├── lib/
│   ├── pdfjs/              # PDF.js 3.11（本地内置）
│   └── highlight.min.*     # highlight.js 11.9（本地内置）
├── converter/
│   └── convert.py          # PDF → HTML 转换器
└── docs/
    └── superpowers/        # 设计规范与实现计划
```

## 🚀 快速开始

### 启动阅读器

```bash
cd 算法书
python -m http.server 3000
# 浏览器打开 http://localhost:3000/index.html
```

> ⚠️ 必须用 HTTP 服务器启动，`file://` 协议会被 CORS 阻止。

### PDF → HTML 转换

```bash
# 转换全部书籍
python converter/convert.py

# 转换指定书籍
python converter/convert.py --book algorithm-contest-2
```

依赖：PyMuPDF（已内置于 `pypkgs/`，无需手动安装）。

## 📖 书籍列表

| 书名 | 作者 | 类型 |
|------|------|------|
| 大话数据结构 | 程杰 | 扫描版 |
| 深入浅出程序设计竞赛（基础篇） | 汪楚奇 | 扫描版 |
| 算法竞赛（上册） | 罗勇军，郭卫斌 | 扫描版 |
| 算法竞赛（下册） | 罗勇军，郭卫斌 | 扫描版 |

## 🛠 技术栈

- **PDF 渲染**：PDF.js 3.11（零 CDN，本地内置）
- **代码高亮**：highlight.js 11.9
- **PDF 转换**：PyMuPDF 1.28
- **纯静态**：无后端，无框架，无构建工具

## 📋 路线图

- [x] Phase 1：静态书架 + PDF.js 阅读器
- [ ] Phase 2：CLI 转换器产品化
- [ ] Phase 3：在线服务（Web 上传 → 转换 → 阅读）

详见 [PROGRESS.md](./PROGRESS.md)。

## 📄 许可

MIT License
