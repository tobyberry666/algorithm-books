# 跨会话记忆 + 下一阶段任务（给新会话接手）

> 本文件身兼两职：① **跨会话的用户记忆载体**（顶部「〇」章节，每次会话末尾往里追加记忆点）；② **项目下一阶段任务清单**（下方一~四，A~E）。
> 新会话只读本文件即可恢复上下文，不必重读一堆零散记忆文件。

## 〇、用户画像与协作偏好（跨会话记忆 · 每次会话末尾在此追加新记忆点）

### 身份与背景
- 称呼：**Toby**。GitHub: `tobyberry666`；git `user.name`=Toby_here；git 邮箱=`broccoli_finding@qq.com`
- 角色：把 WorkBuddy 当 coding / agent 主力用户

### 当前工具 / 模型状态（有时效，约 2026-07-06 起两周）
- 正在用 **混元 Hy3 两周限免**（2026-07-06 起，约两周，无限额度）
- 迁移原因：Claude Code 被封、Codex 太贵 → 转投 WorkBuddy 限免
- 涉及模型 / 工具选型时，**优先推荐 Hy3 / WorkBuddy 方案**

### 沟通风格
- 中文、带梗、有网感（曾用《我不是药神》台词玩梗）；可轻松口语化，不必过于正式

### 协作与工作流偏好（本次会话明确观察到，重要）
- **上下文焦虑**：担心会话上下文长度不够；遇到大任务会主动要求「分会话推进」。→ 长任务主动拆阶段，每阶段收尾写交接文档。
- **Git 工作流**：要求先把 GitHub 连接上、最后统一 `commit`+`push`，**不喜欢中途零散 push**。
  - 本机 `gh` CLI 已登录（token 在 keyring），但 Git 凭据助手默认没接上 → push 前先跑一次 `gh auth setup-git`，之后 `git push origin master` 即可用 gh token 推送（无需另配凭证）。
  - 若 `git push` 报 non-fast-forward：远端可能只多了「Update deployment log」之类自动提交，用 `git fetch && git rebase origin/master` 再 push 即可（线性历史）。
- **记忆管理偏好**：希望跨会话记忆集中到单一文件（本 NEXT_STEPS.md），每次会话末尾往里追加一点，节省上下文。
- 项目物理路径：`F:\大一下文件\算法书`（Windows 中文路径，注意编码）。

### 项目背景速记（algorithm-books）
- 目标：他人 `git clone` → 投放任意扫描版 PDF → 一条命令转成「可复制的自包含 HTML」→ 可滚动网页阅读。
- 已上传 GitHub：`github.com/tobyberry666/algorithm-books`（有 `master` + `gh-pages` 分支）。
- 含 5 本算法书 PDF（4 扫描 + 1 文字 poster）；本机缺 tesseract（OCR 闭环待补）。

---

## 一、上一阶段已完成（无需重做）

- ✅ **阅读器重影修复**：`css/viewer.css` 把 `.textLayer span` 改为 `color: transparent`；`js/viewer.js` 恢复了 `renderTextLayer`，文字 PDF 现在**既能选中复制、又不再双影**。
- ✅ **`converter/convert.py` 完全重写为纯 CLI**：
  - 去掉硬编码路径（不再写死 `F:\大一下文件\算法书`），任何人 clone 后放任意 PDF 即可转。
  - 自动检测「文字版 / 扫描版」（`detect_mode`）。
  - 文字版抽结构化文本（标题/段落/代码块/配图），天然可复制。
  - 扫描版每页渲染高清图；若本机有 tesseract，可 `--ocr` 叠加透明但可选中的 OCR 文字层（`.ocr-layer`）。
  - **输出完全自包含**：CSS/JS 内联，代码高亮用到的 `highlight.min.*` 复制到输出 `assets/`，**不再引用 `../../lib`**。
- ✅ **`requirements.txt`**：`pymupdf` / `pillow` / `pytesseract`。
- ✅ **实测跑通**：`poster.pdf`（文字版）自包含输出 OK（无 `../../lib`、hljs 已复制）；`算法竞赛（下册）`（扫描版）跑通并优雅降级为纯图片（本机无 tesseract）。

---

## 二、待办（宏伟计划剩余部分）

### A. 文档对齐（必须，先做）

1. **重写 `README.md`**：突出核心工作流
   ```
   任何人 clone → 放任意 PDF → python converter/convert.py 你的书.pdf
   → 得到可滚动、可复制的自包含 HTML（converted/<名>/index.html）
   ```
   删掉旧的「PyMuPDF 已内置 pypkgs，无需安装」等说法，改为 `pip install -r requirements.txt`。
   说明 OCR 是可选的（需系统装 tesseract + `chi_sim` 中文包），缺了扫描版退化为纯图片。
2. **更新 `PROGRESS.md`**：
   - 把「禁用 textLayer（因重影）」决策改为「文字层透明化：既无重影又可复制」。
   - 删除「PyMuPDF 本地安装 pypkgs」描述，改为 pip 依赖清单。
   - 标记 Phase 2 已产品化完成。
3. **`handoff.md`**：同样修正过时/矛盾（文字层开关、auto-fix 永远不出现等）。

### B. 书架画廊 + 示范产物

4. `books.json`：给剩余 3 本（`dahua-datastructure` / `shen-ru-qian-chu` / `algorithm-contest-1`）补 `converted` 字段，并实际转换它们。默认 `dpi 110`；若要可复制需先装 tesseract 再 `--ocr`。
5. `.gitignore`：`converted/` 被忽略 → 别人 clone 看不到任何 HTML 示范。建议：**提交 `poster` 作为最小 demo**（小、文字版、证明机制），其余书按需本地生成。或改为在 README 说明「clone 后自行转换」。

### C. OCR 真正闭环（依赖环境）

6. 本机当前**未装 tesseract 二进制**，pytesseract 也未装入 venv。要真正产出「可复制扫描版」需：
   - 安装 python 依赖：`pip install pytesseract pillow`（或装进 managed venv `C:/Users/Toby/.workbuddy/binaries/python/envs/default`）
   - 系统装 tesseract + 中文包 `chi_sim`（Windows 下载安装包并加入 PATH）
   - 实测：`python converter/convert.py 扫描书.pdf --ocr` 应产出带 `.ocr-layer` 的可复制页
   若本机无法装 tesseract，至少在 README 写清步骤，让使用者自行安装即可。

### D. 部署与收尾

7. 检查 `.github/workflows/deploy.yml` 是否适配新产物结构（自包含 HTML 在 `converted/<id>/`）。GitHub Pages 部署路径确认。
8. ⚠️ **容量注意**：扫描版全本转 HTML 会很大（算法竞赛下册 660 张图，`dpi 110` 可能数十 MB）。GitHub Pages 有容量/单文件限制。考虑：降低 `dpi`、或只部署 demo、或文档化「本地转换本地看」。
9. `git add` / `commit` / `push` 当前改动到 `github.com/tobyberry666/algorithm-books`：
   - 已改：`converter/convert.py`、`css/viewer.css`、`js/viewer.js`
   - 新增：`requirements.txt`
   - （`converted/` 被 gitignore，无需提交；如按 B5 决定提交 poster demo 则相应 add）

### E. 远期（Phase 3，可选，用户称「宏伟计划」可包含）

10. Web 上传服务：上传 PDF → 后台跑 `convert.py` → 在线阅读 / 下载 zip。

---

## 三、关键文件现状速查

| 文件 | 状态 |
|------|------|
| `converter/convert.py` | ✅ 已重写：可移植、自包含、OCR 可选 |
| `requirements.txt` | ✅ 已建 |
| `css/viewer.css`、`js/viewer.js` | ✅ 重影已修 |
| `books.json` | 仅 `poster`、`algorithm-contest-2` 有 `converted` 字段 |
| `lib/` | 存在 `highlight.min.*` 和 `pdfjs`（书架/阅读器用；转换器已自带复制逻辑不依赖它） |
| `.gitignore` | 忽略 `pypkgs/` 和 `converted/` |
| `lib/pdfjs` | 仍在，供 `viewer.html` PDF.js 阅读器使用 |

---

## 四、如何接手

新会话直接读本项目 `NEXT_STEPS.md`，按 **A → B → C → D → E** 顺序执行。
当前阶段的转换器与重影修复已经做完并实测，不要重复。

---

## 五、本会话进展（2026-07-07 · Hy3 限免期）

**A→E 全部推进完毕并统一 commit+push 到 `master`（commit `e71a2e4`，已触发 Pages 部署）。**

| 阶段 | 状态 | 关键产出 |
|------|------|----------|
| **A 文档对齐** | ✅ | 重写 `README.md`（核心工作流 + OCR 步骤 + pip 依赖）；`PROGRESS.md` 文字层改「透明化」、pypkgs→pip、Phase 2 标记完成；`handoff.md` 修正（convert.py 正常 CLI、auto-fix 仅文字版生效） |
| **B 书架+demo** | ✅ | 本地转换完剩余 3 本（dahua 151MB / shenru 337MB / ac1 127MB，均 dpi110 扫描版退化为图片，gitignore 不提交）；`books.json` 5 本全补 `converted`；force-add `converted/poster` 作最小 demo |
| **C OCR 闭环** | 🟡 部分 | managed venv 已装 `pytesseract`+`pillow`；**系统 tesseract 二进制本机仍未装** → 扫描版仍走「纯图片优雅降级」。README 已写清安装步骤，装好即可 `--ocr` |
| **D 部署收尾** | ✅ | `deploy.yml` 移除 `converted` 排除（仅 poster 被追踪故只部署 poster demo，大书 gitignored 不进 Pages）；`git add`+`commit`+`push` 一气呵成 |
| **E 远期 Web 服务** | 🟡 脚手架 | 新增 `server/web_app.py`：标准库 http.server 上传→调 `convert.py`→在线阅读/下载 zip，零第三方依赖，可运行 |

**仍待办（留给后续会话 / 用户）**
1. **OCR 真正可用**：本机装 tesseract + `chi_sim`（Windows 用 UB-Mannheim 安装包），重转扫描版即得可复制页。
2. **扫描版全本部署容量**：下册 330 图、shenru 337MB 等，不适合整体上 Pages；维持「本地转换本地看」+ 仅 poster 在线 demo。
3. **E 生产化**：Web 服务需加异步队列、鉴权、上传限制、清理策略（见 `server/web_app.py` 末尾 TODO）。
4. **Push 提示**：本会话发现 `gh` 已登录但 Git 凭据未接线，先 `gh auth setup-git` 再 push（已记入〇章 Git 工作流）。
