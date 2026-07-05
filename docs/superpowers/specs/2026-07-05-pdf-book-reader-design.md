 # PDF Book Reader — 设计文档

## 概述

将个人 PDF 电子书文件夹转换为可动态浏览、可交互的纯静态网页阅读器。核心目标是导航能力 + 文字可复制 + 代码高亮，零服务器依赖，双击即用。

长远目标：分三阶段演化为面向公众的公开项目（GitHub 开源），允许任何人上传长 PDF 一键转换为网页版电子书。

## 阶段规划

1. **第一阶段（当前）**：核心阅读器——纯静态 HTML + PDF.js 书架 + 阅读器
2. **第二阶段**：CLI 转换器——输入 PDF，输出自包含阅读文件夹
3. **第三阶段**：在线服务——Web 上传 → 转换 → 在线阅读

## 技术选型

- **渲染引擎**：PDF.js（Mozilla），本地内置不依赖 CDN
- **代码高亮**：highlight.js，自动语言检测
- **前端框架**：无框架，纯 vanilla JS + ES modules
- **构建**：无构建工具，直接可用

## 文件结构

```
pdf-book-reader/
├── index.html                    ← 入口：书架
├── viewer.html                   ← 阅读器页面
├── books.json                    ← 书籍配置（可手工编辑）
├── css/
│   ├── bookshelf.css
│   └── viewer.css
├── js/
│   ├── bookshelf.js              ← 书架：加载 books.json，渲染封面卡片
│   ├── viewer.js                 ← 核心：初始化 PDF.js、模式切换、布局
│   ├── toc.js                    ← 左侧目录导航面板
│   ├── toolbar.js                ← 顶部工具栏
│   └── utils.js                  ← 共享工具函数
├── lib/
│   └── pdfjs/                    ← PDF.js 库（本地内置）
└── books/                        ← PDF 文件目录
```

## 页面设计

### 书架页 (index.html)

- 读取 `books.json` 配置，按卡片网格排列书籍
- 点击卡片跳转 `viewer.html?book=xxx.pdf`
- 封面来源：PDF 首页自动截图缓存到 localStorage，无封面则显示文字占位
- 响应式布局：桌面 3-4 列，平板 2 列，手机 1 列

**books.json 结构：**

```json
{
  "books": [
    {
      "id": "dahua-datastructure",
      "title": "大话数据结构",
      "author": "程杰",
      "file": "books/大话数据结构.pdf",
      "cover": "books/大话数据结构.jpg"
    }
  ]
}
```

### 阅读器页 (viewer.html)

三区布局：左侧可收起目录 + 中间 PDF 渲染区 + 顶部工具栏。

#### 工具栏
- 书名显示 | 目录切换按钮 | 滚动/翻页切换 | 页码跳转 | 返回书架

#### 滚动模式（默认）
- 所有页面垂直堆叠，连续滚动阅读
- 懒渲染：只渲染可见区域 ± 2 页，滚出视口的 Canvas 回收保留尺寸占位
- 代码块检测后加 highlight.js 语法高亮覆盖层

#### 翻页模式
- 一次渲染一页，居中显示
- 预加载：当前页 ± 1 页预渲染
- 键盘 ← → 翻页，底部页码显示
- 工具栏切换按钮切换回滚动模式

#### 目录导航（左侧面板）
- 从 PDF outline 提取，点击跳转对应页
- 高亮当前可视章节
- 无目录元数据时回退到页码列表
- 可收起/展开

#### 文字复制
- PDF.js textLayer 模式开启，文字为真实 DOM 文本节点，天然可选中复制

#### 代码高亮
- 启发式检测代码块（连续缩进行 + 代码关键词匹配）
- 对检测到的区域覆盖 pre code + highlight.js 着色
- 行内短代码不单独高亮，避免破坏排版

#### 状态保持
- URL hash 记录 page 和 mode，刷新恢复位置和模式

## 数据流

### 书架页

books.json → bookshelf.js → 渲染封面卡片 → 点击 → viewer.html?book=xxx.pdf

### 阅读器页

URL ?book=xxx.pdf → viewer.js → PDF.js 加载 →
  toc.js 接收 outline → 渲染目录 → 点击 → goToPage(n)
  toolbar.js 接收事件 → 模式/页码/返回
  Canvas 渲染（滚动或翻页）

两种模式共享同一个 PDF.js Document 实例，切换模式不需要重新加载。

## 边界处理

- **大 PDF**：PDF.js 流式加载，68MB 无压力
- **file:// 协议**：PDF.js 回退到一次性加载，仍在内存增量解析
- **加载失败**：显示友好错误提示，不白屏
- **中文支持**：textLayer 正确渲染和选中中文
- **无目录 PDF**：回退到页码滑块导航
- **无封面**：自动截 PDF 首页缩略图，localStorage 缓存

## 性能

- 翻页模式：±1 页预渲染，零延迟翻页
- 滚动模式：懒渲染可见 ± 2 页，回收离屏 Canvas
- 缩略图生成仅首次触发，缓存持久化
- PDF.js worker 在 Web Worker 运行，不阻塞主线程

## 依赖

- PDF.js（本地内置）
- highlight.js（本地内置）
- 零 npm / webpack / 服务器
