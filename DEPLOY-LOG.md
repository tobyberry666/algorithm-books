# GitHub Pages 部署踩坑全记录

> 日期：2026-07-05 | 项目：算法书 PDF Book Reader

---

## 背景

将本地项目 `F:\大一下文件\算法书` 推送到 GitHub 并部署到 GitHub Pages。

项目特点：
- 纯静态 HTML/CSS/JS（PDF.js 阅读器 + 书架）
- 5 本 PDF 共约 160MB（Git LFS 管理）
- 最大单文件 68MB

---

## 时间线

### 第一关：Git 初始化 + LFS 配置 ✅

```
git init → git lfs track "*.pdf" → git add -A → git commit
```

- 配置 `user.name = Toby_here`，`user.email = broccoli_finding@qq.com`
- 创建 `.gitignore`（排除 node_modules、pypkgs、converted）
- `gh repo create algorithm-books --public --push`
- LFS 上传 5 本 PDF（166MB）

**结果**：仓库创建成功，代码 + PDF 全部推送。

### 第二关：GitHub Pages 部署 ❌→❌→❌→✅

#### 尝试 1：Actions + upload-pages-artifact（无 LFS）

```yaml
# 问题：没有 lfs: true，PDF 是 LFS 指针文件
steps:
  - uses: actions/checkout@v4        # ❌ 缺 lfs: true
  - uses: actions/upload-pages-artifact@v3
  - uses: actions/deploy-pages@v4
```

**结果**：部署成功，但 PDF 全是 LFS 指针（约 130 字节），PDF.js 报 `Invalid PDF structure`。

#### 尝试 2：加 lfs: true

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      lfs: true                      # ✅ 加了
  - uses: actions/upload-pages-artifact@v3
  - uses: actions/deploy-pages@v4
```

**结果**：LFS 文件确实拉取了（验证步骤确认 PDF 头正确），但 `deploy-pages` 在 `syncing_files` 阶段报 `Deployment failed, try again later`。

**根因**：5 本 PDF 共 160MB，超过了 `deploy-pages` Action 的承载能力。

#### 尝试 3：PDF 放 GitHub Releases，网站放 Pages ❌

- 创建 Release v0.1.0，上传 5 本 PDF
- `books.json` 中 `file` 指向 Release 直链
- Pages 只部署网站代码

**结果**：`Access to fetch ... has been blocked by CORS policy`。

**根因**：GitHub Releases 下载链接没有 `Access-Control-Allow-Origin` 头，跨域请求被浏览器拦截。

#### 尝试 4：gh-pages 分支部署 ✅

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      lfs: true
  - uses: peaceiris/actions-gh-pages@v4   # 直接 git push 到 gh-pages
    with:
      publish_dir: .
      force_orphan: true
```

同时用 API 切换 Pages 源：
```
gh api .../pages -X PUT -F "source[branch]=gh-pages" -F "build_type=legacy"
```

**关键坑**：`build_type` 之前是 `workflow`，需要改为 `legacy`，否则 Pages 不会从分支自动构建。

**结果**：✅ 网站 + PDF 同域部署，无 CORS 问题，全部正常。

---

## 根因分析

| 方案 | 失败原因 |
|------|----------|
| `upload-pages-artifact` 无 LFS | PDF 文件内容为 LFS 指针，不是真实 PDF |
| `upload-pages-artifact` + LFS | 160MB 总量超出部署管道限制 |
| GitHub Releases + Pages | Releases 没有 CORS 头，跨域被拦截 |
| `gh-pages` 分支 + `build_type=legacy` | ✅ 同域 + 走 git push，无体积限制 |

---

## 最终架构

```
git push → master 分支
              ↓
     GitHub Actions (deploy.yml)
              ↓
     checkout (lfs: true) → 拉取真实 PDF
              ↓
     peaceiris/actions-gh-pages@v4
              ↓
     git push → gh-pages 分支
              ↓
     GitHub Pages (build_type=legacy)
              ↓
     https://tobyberry666.github.io/algorithm-books/
```

---

## 教训

1. **Git LFS + GitHub Pages 是经典踩坑组合**。`upload-pages-artifact` 对大文件不友好。
2. **GitHub Releases 不适合做前端资源**。没有 CORS 头，浏览器无法跨域 fetch。
3. **gh-pages 分支 + legacy 构建** 是最稳定的 Pages 部署方式，尤其适合包含大文件的静态站点。
4. **PDF.js 的 `Invalid PDF structure` 错误** 不一定是文件损坏，也可能是拿到了 LFS 指针或 HTTP 错误页。
5. **`build_type` 切换是静默陷阱**：从 workflow 切到 legacy 必须显式传参，否则 Pages 傻等一个不会来的 Action。

---

## 本次会话同时完成

- 5 条 Issues（三阶段路线 + 待办）
- GitHub Actions 自动部署工作流
- Projects 看板「算法书 — 开发路线图」
- Wiki 4 页文档
- README.md
- Release v0.1.0
