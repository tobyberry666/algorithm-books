 # PDF Book Reader — 项目交接文档
 
 > 编写日期：2026-07-05 | 目标读者：接手此项目的开发者
 
 ## 一、项目目标
 
 将文件夹中的中文 PDF 算法教材（4 本）转换为可动态浏览、可交互的纯静态网页，后续发展为面向公众的开源项目。
 
 **三阶段路线：**
 1. **Phase 1（当前）**：核心阅读器 — 纯静态 HTML + PDF.js，书架 + 阅读器
 2. **Phase 2**：CLI 转换器 — 输入 PDF → 输出自包含阅读文件夹
 3. **Phase 3**：在线服务 — Web 上传 → 转换 → 在线阅读
 
 ---
 
 ## 二、文档索引
 
 | 文档 | 路径 | 说明 |
 |------|------|------|
 | 设计规范 | `docs/superpowers/specs/2026-07-05-pdf-book-reader-design.md` | 完整需求、架构、组件设计 |
 | 实现计划 | `docs/superpowers/plans/2026-07-05-pdf-book-reader.md` | 分任务实现步骤（仅供参考，实际路径有偏离） |
 | 本文档 | `handoff.md` | 当前状态与待办 |
 
 ---
 
 ## 三、项目结构
 
 ```
 F:\大一下文件\算法书\
 ├── index.html                  ← [OK] 书架入口
 ├── viewer.html                 ← [OK] 阅读器页面
 ├── books.json                  ← [OK] 书籍配置
 ├── handoff.md                  ← 本文档
 │
 ├── css/
 │   ├── bookshelf.css           ← [OK] 书架样式
 │   └── viewer.css              ← [OK] 阅读器样式（textLayer 已可见）
 │
 ├── js/
 │   ├── utils.js                ← [OK] 工具函数
 │   ├── bookshelf.js            ← [OK] 书架逻辑（封面从 PDF 首页截取）
 │   ├── viewer.js               ← [OK] 核心：PDF 渲染、滚动/翻页、代码高亮
 │   ├── toc.js                  ← [OK] 目录导航（从 PDF outline 提取）
 │   └── toolbar.js              ← [OK] 工具栏交互
 │
 ├── lib/
 │   ├── pdfjs/
 │   │   ├── pdf.min.js          ← [OK] PDF.js 3.11.174（从 npm 安装）
 │   │   └── pdf.worker.min.js   ← [OK] Worker
 │   ├── highlight.min.js        ← [OK] 代码语法高亮 (121KB)
 │   └── highlight.min.css       ← [OK] 高亮主题
 │
 ├── converter/
 │   └── convert.py              ← [BROKEN] PDF→HTML 转换脚本（缩进错误，需修复）
 │
 ├── pypkgs/
 │   └── fitz/                   ← [OK] PyMuPDF 1.28.0（PDF 文本提取库）
 │
 ├── converted/                  ← [待生成] 转换后的 HTML 书籍输出目录
 │
 └── *.pdf                       ← 4 本原始 PDF 书籍
     ├── 大话数据结构 (程杰) — 45MB
     ├── 深入浅出程序设计竞赛（基础篇）(汪楚奇) — 68MB
     ├── 算法竞赛（上册）(罗勇军，郭卫斌) — 27MB
     └── 算法竞赛（下册）(罗勇军，郭卫斌) — 19MB
 ```
 
 ---
 
 ## 四、当前状态：已完成
 
 ### 1. PDF.js 阅读器（Phase 1 核心）
 
 - 书架页：4 本书的封面卡片，从 PDF 首页自动截取缩略图（localStorage 缓存）
 - 滚动模式（默认）：全文连续垂直滚动，懒渲染（IntersectionObserver）
 - 翻页模式：单页居中显示，自适应 viewport 缩放，键盘 ← → 翻页，点击左右半区翻页
 - 目录导航：从 PDF outline 提取章节树，点击跳转；无 outline 时回退到页码列表
 - 文字层：textLayer 可见，所有文字可选中、可 Ctrl+C 复制
 - 代码高亮：启发式检测代码块（缩进 + 关键词匹配），hljs.highlightAuto 自动着色
 - URL hash 状态保持：刷新页面恢复页码和阅读模式
 
 ### 2. 基础设施
 
 - PDF.js 3.11.174 本地内置（`lib/pdfjs/`），零 CDN 依赖
 - highlight.js 11.9.0 本地内置（`lib/`），零 CDN 依赖
 - PyMuPDF 1.28.0 安装到 `pypkgs/`（用于转换器）
 
 ---
 
 ## 五、待完成
 
 ### 🔴 优先级 1：修复并运行 PDF→HTML 转换器
 
 **文件**：`converter/convert.py`
 
 **问题**：脚本有缩进错误，无法运行。原因是用 `Out-File` 写文件时引入了额外缩进。
 
 **修复步骤**：
 
 1. 用编辑器打开 `converter/convert.py`
 2. 确认第 2 行 docstring 前无空格（`"""PDF to HTML..."""` 而非 ` """PDF to HTML..."""`）
 3. 确认 `import fitz` 在第 4 行无额外缩进
 4. 删除重复的 `import sys` 行（patch 导致重复导入）
 5. 确保 `sys.path.insert(0, ...)` 在所有 import 之后、ROOT 定义之前
 
 **运行方式**：
 
 ```powershell
 $env:PYTHONPATH = "F:\大一下文件\算法书\pypkgs"
 python "F:\大一下文件\算法书\converter\convert.py"
 ```
 
 脚本会读取 `books.json`，对每本书做以下操作：
 1. 用 PyMuPDF 提取每页的文字块和图片
 2. 检测代码块（缩进 + 关键词启发式匹配）
 3. 生成一个 `converted/<book-id>/index.html` 文件：
    - 左侧：章节导航侧边栏（从 PDF outline）
    - 右侧：全文本 + 图片 + 代码块的 HTML 页面
    - 代码块包裹在 `<pre><code>` 中，hljs 自动着色
 
 **预期输出**：
 ```
 converted/
 ├── dahua-datastructure/
 │   └── index.html
 ├── shen-ru-qian-chu/
 │   └── index.html
 ├── algorithm-contest-1/
 │   └── index.html
 └── algorithm-contest-2/
     └── index.html
 ```
 
 **⚠️ 注意事项**：
 - 转换后可能有排版问题（尤其数学公式区域），需人工逐页检查
 - 图片会以 base64 内嵌，导致 HTML 文件较大（每本书 10-50MB）
 - 大型 PDF（68MB 的深入浅出）转换时间可能较长（10-30 分钟）
 
 ### 🟡 优先级 2：更新书架链接到转换版
 
 转换器跑通后，更新 `books.json` 加 `converted` 字段 → 更新 `bookshelf.js` 加"HTML 版"按钮。
 
 ### 🟡 优先级 3：人工修正转换质量
 
 逐页检查转换内容，重点修正：
 - 数学公式/符号丢失或乱码
 - 代码块误判（正常段落被识别为代码，或代码未被识别）
 - 图片错位
 - 目录链接指向错误的章节
 
 ### 🟢 优先级 4：启动测试
 
 ```powershell
 python -m http.server 3000 --directory "F:\大一下文件\算法书"
 # 浏览器打开 http://localhost:3000/index.html
 ```
 
 ---
 
 ## 六、已知问题 & 注意事项
 
 1. **`file://` 协议不支持**：ES modules 和 `fetch()` 在 `file://` 下会被 CORS 阻止。必须用 HTTP 服务器。
 
 2. **In-app 浏览器无法测试**：Codex 内置浏览器对 `localhost` 和 `file://` URL 有限制。测试请在系统默认浏览器（Chrome/Edge）中手动进行。
 
 3. **`apply_patch` 的 `*** Move to` 陷阱**：对同一路径使用 `*** Move to` 会导致文件被删除。后续编辑文件请使用 `*** Update File` + `@@` 行匹配，不要加 `*** Move to`。
 
 4. **PyMuPDF 安装位置**：模块安装在 `pypkgs/` 中而非系统 site-packages，因为沙箱无法读取 `C:\Python314\Lib\site-packages`。运行转换脚本时需要确保 `sys.path` 包含此路径。
 
 5. **书籍文件路径**：PDF 在项目根目录，`books.json` 中的 `file` 字段用相对路径（如 `"算法竞赛（下册）...pdf"`）。
 
 ---
 
 ## 七、关键技术决策
 
 | 决策 | 原因 |
 |------|------|
 | PDF.js 而非原生渲染 | 保留原书排版（公式、图表零损失），避免转换失真 |
 | `<script>` 加载 PDF.js 而非 ES module import | npm 输出的 pdf.js 是 UMD 格式（`.js`），不是 ES module（`.mjs`） |
 | 本地内置所有依赖 | 沙箱和 in-app 浏览器均无法访问 CDN |
 | PyMuPDF 而非 pdfplumber | pdfplumber pip 安装超时；PyMuPDF 更轻量更快 |
 | 单页 HTML（全本书在一个页面）而非多页 | labuladong.online 风格，侧边栏章节跳转 = 页内锚点导航 |
 
 ---
 
 ## 八、后续 Phase 2/3 简要方向
 
 - **Phase 2 (CLI 转换器)**：将 `converter/convert.py` 打磨为命令行工具 `pdf-to-html input.pdf --output ./my-book/`，输出自包含文件夹（含 reader HTML + 转换后的内容）
 - **Phase 3 (在线服务)**：在 converter 外包装 Web UI，用户上传 PDF → 后台转换 → 返回在线阅读链接或下载 zip
