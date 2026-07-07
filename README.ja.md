# 📚 算法書（Algorithm Books） — PDF 教材を「スクロール・コピー可能」な自己完結型 Web ページに

> 1 コマンドで任意の PDF（テキスト版／スキャン版）を、外部リソースに依存しない HTML リーダーに変換します。
> さらに、オリジナル PDF をその場で読める静的本棚 ＋ PDF.js ビューアを内蔵しています。

**一番の特長**：`git clone` → 読みたい PDF をフォルダに放り込む → 1 コマンド →
**スクロール・選択コピー可能、ダブルクリックで開く**自己完結型 HTML（`converted/<書名>/index.html`）が完成。
リポジトリの `lib/` は一切参照しないので、任意の静的サーバーや GitHub Pages にそのまま置けます。

---

## ✨ 2 つの読書モード

| モード | コマンド／入口 | 向いている用途 | テキストコピー |
|------|------------|------|----------|
| **A. 変換後の HTML** | `python converter/convert.py あなたの本.pdf` | 長期読書、引用をコピーしたい | ✅ テキスト版は元からコピー可；スキャン版は tesseract 導入でコピー可に |
| **B. PDF.js オリジナルビューア** | `index.html` を開く → 「PDF 版」をクリック | 原本のレイアウト・数式を確認 | ✅ テキスト層を透明化しつつ選択可能に |
| **本棚ギャラリー** | `index.html` を開く | 本棚から選書 | — |

> どちらのモードも純静的：バックエンドなし、CDN なし。

---

## 🚀 クイックスタート

### 1. 依存関係をインストール

```bash
pip install -r requirements.txt
```

- `pymupdf`：**必須**、PDF の解析とレンダリング（`fitz` を提供）。
- `pillow` + `pytesseract`：**OCR 用**、スキャン版をコピー可能にしたい場合のみ必要。
- リポジトリには `pypkgs/fitz` をフォールバックとして同梱。上記 pip パッケージを入れればそちらが使われます（どちらでも可）。

### 2. 任意の PDF を自己完結型 HTML に変換

```bash
# 最も一般的：単一 PDF を変換（「テキスト版／スキャン版」を自動判別）
python converter/convert.py わたしの本.pdf

# 出力先ディレクトリと書名を指定
python converter/convert.py わたしの本.pdf -o ./out/わたしの本 --title "わたしの本"

# スキャン版をコピー可能にしたい？ まず tesseract を導入（下記「OCR について」参照）、その後 OCR を有効化
python converter/convert.py スキャン本.pdf --ocr --lang chi_sim+eng
```

変換すると以下が生成されます：

```
converted/わたしの本/
├── index.html        # 自己完結型：CSS/JS をインライン展開、コードハイライト用 hljs も内包
├── images/           # 各ページの画像（スキャン版）または図版（テキスト版）
└── assets/           # highlight.min.*（テキスト版のみ）
```

ブラウザで `converted/わたしの本/index.html` を開けば読めます（HTTP サーバー推奨。
`file://` では一部ブラウザがリソース読み込みを制限します）。

### 3. 本棚ギャラリー（PDF.js ビューア）を使う

```bash
python -m http.server 3000
# ブラウザで http://localhost:3000/index.html を開く
```

> ⚠️ HTTP サーバー経由で起動すること。 `file://` プロトコルは CORS によってブロックされます。

---

## 🔤 OCR について（スキャン版をコピー可能にする鍵）

スキャン版 PDF にはテキストが埋め込まれていないため、初期状態では「1 ページにつき 1 枚の高解像度画像」に変換され、
**テキストを選択・コピーできません**。コピー可能にするには OCR が必要です：

1. **tesseract バイナリをシステムに導入**し、`PATH` に追加：
   - Windows：[UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) のインストーラーで、中国語パック `chi_sim` にチェック。
   - macOS：`brew install tesseract tesseract-lang`
   - Linux：`sudo apt install tesseract-ocr tesseract-ocr-chi-sim`
2. Python 依存を導入：`pip install pytesseract pillow`（すでに `requirements.txt` にあり）。
3. 再変換：`python converter/convert.py スキャン本.pdf --ocr`。

変換後のスキャン页には、画像に**位置合わせされ、透明だが選択可能な OCR テキスト層**（`.ocr-layer`）が重ねられ、
スキャン本もテキスト本と同じように Ctrl+C でコピーできるようになります。

> この環境に tesseract が入っていない？ 問題ありません。コンバータは**単なる画像に優雅に退化**し、
> ページ最上部に OCR を有効化する方法を表示します。

---

## 📂 プロジェクト構成

```
算法书/
├── index.html              # [ギャラリー] 本棚の入り口
├── viewer.html             # [Phase 1] PDF.js ビューア
├── books.json              # 書籍設定（本棚＋一括変換用）
├── converter/
│   └── convert.py          # [Phase 2] PDF → 自己完結型 HTML コンバータ（純 CLI）
├── requirements.txt        # pip 依存リスト
├── lib/                    # 本棚／ビューア用 pdfjs ＋ highlight.js（コンバータは非依存）
├── css/  js/               # 本棚とビューアのスタイル／ロジック
├── pypkgs/                 # PyMuPDF フォールバック（gitignore、pip 導入を推奨）
└── converted/              # 変換出力（gitignore；poster のみ最小デモとしてデプロイ）
    └── poster/             # テキスト版デモ（GitHub Pages にデプロイ済み）
```

---

## 📖 収録書籍

| 書名 | 種別 | PDF | HTML |
|------|------|--------|---------|
| Poster | テキスト型（1 ページ） | ✅ | ✅ デプロイ済み（最小デモ） |
| 大话数据结构（やさしいデータ構造） | スキャン版 | ✅ | ローカル変換で利用可 |
| 深入浅出程序设计竞赛（基础篇）（競技プログラミング入門） | スキャン版 | ✅ | ローカル変換で利用可 |
| 算法竞赛（上册）（アルゴリズム競技 上） | スキャン版 | ✅ | ローカル変換で利用可 |
| 算法竞赛（下册）（アルゴリズム競技 下） | スキャン版 | ✅ | ローカル変換で利用可 |

> `converted/` は gitignore されています：**クローン直後は poster デモのみがオンラインで見えます**。
> その他の本はローカルで `python converter/convert.py --batch` を実行して生成してください（本棚ギャラリーは維持）。

---

## 🛠 技術スタック

- **PDF レンダリング**: PDF.js 3.11（CDN ゼロ、ローカル同梱）
- **コードハイライト**: highlight.js 11.9
- **PDF 変換**: PyMuPDF 1.28（コンバータの中核）
- **純静的**: バックエンドなし、フレームワークなし、ビルドツールなし

---

## 📋 ロードマップ

- [x] **Phase 1**: 静的本棚 ＋ PDF.js ビューア（スクロール／ページ送り／目次／コードハイライト）
- [x] **Phase 2**: CLI コンバータの製品化（移植性・自己完結・OCR 任意）
- [ ] **Phase 3**: オンラインサービス（Web アップロード → 変換 → オンライン読書／zip ダウンロード）— `server/` 参照

詳細は [PROGRESS.md](./PROGRESS.md) および [handoff.md](./handoff.md) を参照。

---

## 📄 ライセンス

MIT License
