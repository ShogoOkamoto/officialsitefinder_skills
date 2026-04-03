こ# officialsitefinder_skills — プロジェクト統合文書

> 最終更新: 2026-03-19 (v6 対応)

---

## 1. プロジェクト概要

### 目的

日本の施設（企業・店舗・観光地・医療機関など）の **公式サイトのトップページURL** を、施設名と住所から自動発見するシステム。

### 解決する課題

- 施設名だけでは同名施設が複数存在し、誤ったサイトを採用するリスクがある
- Google検索で上位に出るサイトが公式サイトとは限らない（ポータルサイト・予約サイトなど）
- 住所照合によって「同じ施設のサイトか」を客観的に検証する

### v6 時点での状態（2026-02-28）

| バージョン | 主な追加・変更 |
|---|---|
| v1〜v3 | 初期実装、基本ワークフロー |
| v4 | Claude API直接呼び出しを廃止、Claude Codeサブエージェント活用 |
| v5 | criteria.txt による公式サイト判定ステップ（手順7）追加 |
| **v6** | 手順2を2段階化（フル住所 + 市区町村住所）、検索クエリを市区町村レベルに変更 |

---

## 2. アーキテクチャ図

```
ユーザー入力: 施設名 + 住所
       │
       ▼
┌──────────────────────────────────────────────────┐
│          officialsite_finder_tool (メイン)         │
│                                                    │
│  手順2-A ──► extract_full_address_tool             │
│              └► フル住所（照合用）                  │
│  手順2-B ──► extract_address_tool (旧版)           │
│              └► 市区町村住所（検索クエリ用）         │
│                                                    │
│  手順3  ──► google_search_tool                     │
│              └► 検索結果 (最大5件のURL)             │
│                                                    │
│  手順4  ──► playwright_download_tool               │
│              └► HTMLテキスト                        │
│                                                    │
│  手順5  ──► extract_full_address_tool              │
│              └► ページ内住所リスト                  │
│                                                    │
│  手順6  ──► compare_address_full_tool              │
│              └► 住所マッチ判定                      │
│                                                    │
│  手順7  ──► [Task サブエージェント]                 │
│              └► criteria.txt 収集対象判定           │
│                                                    │
│  手順8  ──► [Task サブエージェント]                 │
│              └► トップページ判定                    │
└──────────────────────────────────────────────────┘
       │
       ▼
出力: { success, official_site_url, matched_address }


Claude Code スキル層
┌────────────────────────────────────┐
│  officialsite_finder_skill  ⭐     │ ← /officialsite-finder
│  extract_full_address_skill        │ ← /extract-full-address
└────────────────────────────────────┘

```

---

## 3. 各ツール詳細仕様

### 3.1 google_search_tool

**場所**: `google_search_tool/`
**役割**: Google Custom Search API を使ったウェブ検索CLIツール

#### 入力

```bash
python -m google_search_tool "クエリ文字列" [-n 件数] [--pretty]
```

| パラメータ | 必須 | 説明 |
|---|---|---|
| `query` | ○ | 検索クエリ文字列 |
| `-n` / `--num-results` | - | 取得件数（1〜10、デフォルト: 10） |
| `--pretty` | - | JSON整形出力 |

#### 出力（JSON）

```json
{
  "results": [
    {
      "title": "東京タワー公式サイト",
      "link": "https://www.tokyotower.co.jp/",
      "snippet": "東京タワーの観光情報..."
    }
  ],
  "count": 1
}
```

#### 環境変数

| 変数名 | 説明 |
|---|---|
| `GOOGLE_API_KEY` | Google Cloud API キー |
| `GOOGLE_CSE_ID` | Custom Search Engine ID |

#### 注意事項

- Windows環境でのstdout二重ラップ防止: `sys.stdout is sys.__stdout__` ガードを使用
- エラー時は `{"error": "..."}` を返し、終了コード 1

---

### 3.2 extract_full_address_tool

**場所**: `extract_full_address_tool/`
**役割**: 日本語テキストから番地まで含むフル住所を正規表現で抽出

#### 入力

```bash
# stdin からテキスト読み込み
echo "本社は東京都渋谷区道玄坂1丁目2番3号です" | python -m extract_full_address_tool.extract

# ファイルから読み込み
python -m extract_full_address_tool.extract input.txt
```

#### 出力（JSON配列）

```json
["東京都渋谷区道玄坂1丁目2番3号", "大阪府大阪市北区梅田2-4-9"]
```

#### 抽出対象

- 都道府県 + 市区町村 + 丁目・番地・号（または hyphenated 形式）
- 都道府県 + 郡 + 町村 にも対応
- 番地がない場合は都道府県〜市区町村レベルで抽出

#### Python API

```python
from extract_full_address_tool.extract import extract_full_addresses, extract_full_addresses_list

# JSON文字列を返す
json_str = extract_full_addresses("東京都港区芝公園4-2-8 にある施設")

# Python リストを返す
addresses = extract_full_addresses_list("東京都港区芝公園4-2-8 にある施設")
# → ["東京都港区芝公園4-2-8"]
```

---

### 3.3 compare_address_full_tool

**場所**: `compare_address_full_tool/`
**役割**: 日本語住所の正規化・比較（旧 `compare_address_tool` の上位互換）

#### 入力

```bash
python -m compare_address_full_tool "東京都港区芝公園4-2-8" "東京都港区芝公園4丁目2番8号"
```

#### 出力

| 結果 | 終了コード |
|---|---|
| 一致（exact / prefix match） | 0 |
| 不一致 | 1 |

#### 正規化仕様

1. 空白除去（全角スペース含む）
2. NFKC正規化（全角→半角など）
3. マイナス記号（U+2212）→ ハイフン（U+002D）
4. 漢数字→アラビア数字（一→1、十一→11、二十→20）
5. 番地表記統一（1丁目2番3号 → 1-2-3）
6. 小文字化

#### マッチング戦略

- **完全一致**: 正規化後の文字列が一致
- **前方一致**: 一方が他方のプレフィックスである（詳細度の違いを吸収）

```python
# 例
compare_addresses("東京都港区芝公園4-2-8", "東京都港区芝公園4丁目2番8号")  # → True（表記ゆれ）
compare_addresses("東京都港区芝公園4-2-8", "東京都港区")                   # → True（包含マッチ）
compare_addresses("東京都港区", "大阪府大阪市")                            # → False
```

#### Python API

```python
from compare_address_full_tool import compare_addresses, normalize_address, get_normalized_diff

# 比較（bool）
result = compare_addresses("東京都港区芝公園4-2-8", "東京都港区")
# → True

# 詳細情報
diff = get_normalized_diff("東京都港区芝公園4-2-8", "東京都港区")
# {
#   "equal": True,
#   "match_type": "address2_is_prefix",
#   "address1_original": "東京都港区芝公園4-2-8",
#   "address2_original": "東京都港区",
#   "address1_normalized": "東京都港区芝公園4-2-8",
#   "address2_normalized": "東京都港区"
# }
```

#### compare_address_tool との違い

| 機能 | compare_address_tool（旧版） | compare_address_full_tool（現行） |
|---|---|---|
| 漢数字正規化 | なし | あり（一→1、十一→11） |
| 番地表記統一 | なし | あり（1丁目2番3号→1-2-3） |
| 前方一致・包含マッチ | なし | あり |
| `get_normalized_diff()` | なし | あり（match_type フィールド付き） |

> `compare_address_tool`（旧版）は `compare_address_tool/` に残存しているが、
> `officialsite_finder_tool` では `compare_address_full_tool` を使用している。

---

### 3.4 officialsite_finder_tool

**場所**: `officialsite_finder_tool/`
**役割**: 公式サイト発見のメイン統合ツール（v6フロー11ステップ）

#### 基本実行

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
```

#### 全コマンドラインオプション

| オプション | 説明 |
|---|---|
| `--name` | 施設名称（必須） |
| `--address` | 施設住所（必須） |
| `--judgment` | トップページ判定結果（`Yes`/`No`） |
| `--pending-url` | トップページ判定待ちURL |
| `--criteria-judgment` | 公式サイト判定結果（`eligible`/`not_eligible`） |
| `--criteria-pending-url` | 公式サイト判定待ちURL |
| `--criteria-file` | criteria.txt のパス（デフォルト: `./criteria.txt`） |
| `--matched-address` | 照合済み住所（判定後の再実行時に引き継ぎ） |
| `--skip-urls` | スキップするURL一覧（JSON配列） |
| `--search-results` | Google検索結果の再利用（JSON配列） |
| `--target-address` | 抽出済み対象住所（住所抽出をスキップ） |

#### 処理フロー詳細（v6 11ステップ）

```
手順1  入力検証（施設名・住所が空でないか）
  │
手順2  住所の2段階抽出
  ├─ 2-A: extract_full_address_tool → フル住所（手順6照合用）
  └─ 2-B: extract_address_tool → 市区町村住所（手順3検索用）
  │         ※ v6変更点
手順3  Google検索: "{施設名} {市区町村住所}" で5件取得
  │         ※ v6変更点（番地をクエリから除外）
手順4  playwright_download_tool でHTMLテキスト取得
  │
手順5  extract_full_address_tool でページ内住所を抽出
  │
手順6  compare_address_full_tool でフル住所と照合
  │
手順7  [criteria.txt が存在する場合] サブエージェントで収集対象判定
  │   → request_criteria_judgment アクション出力 → 再実行
  │
手順8  トップページ判定
  ├─ URL構造チェック（ドメイン直下ならOK）
  └─ サブエージェントによる判定
      → request_judgment アクション出力 → 再実行
  │
手順9  [トップページでない場合] ドメインルートに遷移して再判定
  │
手順10 失敗終了 → {"success": false, ...}
手順11 成功終了 → {"success": true, "official_site_url": ..., ...}
```

#### 出力形式

**成功時:**
```json
{
  "success": true,
  "facility_name": "東京タワー",
  "input_address": "東京都港区芝公園4-2-8",
  "official_site_url": "https://www.tokyotower.co.jp/",
  "matched_address": "東京都港区芝公園4-2-8",
  "message": "公式サイトのトップページを発見しました"
}
```

**失敗時:**
```json
{
  "success": false,
  "facility_name": "施設名",
  "input_address": "入力された住所",
  "message": "公式サイトが見つかりませんでした（具体的な理由）"
}
```

**サブエージェント判定依頼（criteria判定）:**
```json
{
  "action": "request_criteria_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/about",
  "html_text_preview": "【先頭5000文字】",
  "criteria": "【criteria.txt全文】",
  "question": "このページは criteria.txt の「URL収集対象」に該当しますか？...",
  "matched_address": "東京都港区芝公園4-2-8",
  "search_results": [...],
  "target_address": "東京都港区"
}
```

**サブエージェント判定依頼（トップページ判定）:**
```json
{
  "action": "request_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/about",
  "html_text_preview": "【先頭5000文字】",
  "question": "このページは「東京タワー」の公式サイトのトップページですか？...",
  "matched_address": "東京都港区芝公園4-2-8"
}
```

#### タイムアウト設定

| 処理 | タイムアウト |
|---|---|
| HTMLダウンロード | 30秒 |
| Google検索API | 30秒 |
| 住所抽出・比較 | 10秒 |
| サブエージェント判定 | 60秒 |
| 全体処理 | 15分 |

---

### 3.5 playwright_download_tool

**場所**: `playwright_download_tool/`
**役割**: Playwright でJavaScriptレンダリング済みのHTMLをダウンロードし、BeautifulSoup でプレーンテキストを抽出

#### 入力

```bash
python download.py "https://example.com/" --format=text
python download.py "https://example.com/" --format=html
```

| パラメータ | 説明 |
|---|---|
| URL | 取得対象URL（必須） |
| `--format` | `text`（デフォルト）または `html` |

#### 出力

- 標準出力にプレーンテキストまたはHTML文字列
- エラー時は終了コード 1

---

## 4. Claude Code スキル

**場所**: `.claude/skills/`

### 4.1 officialsite_finder_skill ⭐

**起動コマンド**: `/officialsite-finder`
**許可ツール**: `Bash(python:*)`, `Task`

スキルのフロー:

1. ユーザーから施設名と住所を取得
2. `python -m officialsite_finder_tool --name "..." --address "..."` を実行
3. JSON出力の `action` フィールドを確認:
   - `request_criteria_judgment` → Task サブエージェントで収集対象判定 → 結果を `--criteria-judgment` で渡して再実行
   - `request_judgment` → Task サブエージェントでトップページ判定 → 結果を `--judgment` で渡して再実行
   - `success: true/false` → 最終結果をユーザーに報告
4. ループを `success` が出るまで繰り返す

**実行例（東京タワー）:**

```
# Run 1: 初回実行
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
→ {"action": "request_criteria_judgment", "url": "https://starrise-tower.com/", ...}

# Task サブエージェントが判定: "not_eligible"

# Run 2: not_eligible の場合（search_results を再利用してGoogle検索をスキップ）
python -m officialsite_finder_tool \
  --name "東京タワー" --address "東京都港区芝公園4-2-8" \
  --criteria-judgment "not_eligible" \
  --criteria-pending-url "https://starrise-tower.com/" \
  --search-results '[...Run1のsearch_results...]' \
  --target-address "東京都港区" \
  --skip-urls '["https://starrise-tower.com/"]'
→ {"action": "request_criteria_judgment", "url": "https://www.tokyotower.co.jp/", ...}

# Task サブエージェントが判定: "eligible"

# Run 3: eligible の場合
python -m officialsite_finder_tool \
  --name "東京タワー" --address "東京都港区芝公園4-2-8" \
  --criteria-judgment "eligible" \
  --criteria-pending-url "https://www.tokyotower.co.jp/" \
  --matched-address "東京都港区"
→ {"success": true, "official_site_url": "https://www.tokyotower.co.jp/", ...}
```

---

### 4.2 extract_full_address_skill

**起動コマンド**: `/extract-full-address`

日本語テキストからフル住所を抽出するスキル。`extract_full_address_tool` のラッパー。

---

## 5. セットアップ手順

### 5.1 前提条件

- Python 3.10 以上
- Google Custom Search API 認証情報:
  - [Google Cloud Console](https://console.cloud.google.com/) で API キーを取得（Custom Search API を有効化）
  - [Programmable Search Engine](https://programmablesearchengine.google.com/) でカスタム検索エンジンIDを取得

### 5.2 インストール

```bash
# リポジトリのルートへ移動
cd officialsitefinder_skills

# 通常インストール
pip install -e .

# 開発用（テスト依存含む）
pip install -e ".[dev]"
```

### 5.3 環境変数の設定

```bash
# テンプレートからコピー
cp .env.example .env
```

`.env` を編集:

```env
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_CSE_ID=your-custom-search-engine-id-here
```

### 5.4 Playwright のセットアップ

```bash
playwright install chromium
```

### 5.5 criteria.txt（オプション）

プロジェクトルートに `criteria.txt` を配置することで、手順7の収集対象判定が有効になる。
ファイルが存在しない場合は手順7をスキップして手順8に進む。

**収集対象（criteria.txtより抜粋）:**
- 施設単独サイトのトップページ
- 法人・グループサイト内の個別施設紹介ページ
- 自治体サイト内の公営施設ページ

**収集対象外:**
- ポータルサイト、予約サイト
- ブログやSNS
- 法人・グループサイトのトップページ

---

## 6. テスト情報

### 6.1 テスト実行方法

Windowsのimport mode非互換のため、**2グループに分けて実行**する。

#### グループ1（デフォルト実行）

```bash
pytest extract_full_address_tool/test_extract.py \
       compare_address_full_tool/test_compare_address_full.py \
       compare_address_tool/tests/test_compare_address.py \
       playwright_download_tool/test_extract.py \
       .claude/skills/extract_full_address_skill/test_skill.py
```

#### グループ2（importlib モード）

```bash
pytest tests/test_google_search_mcp.py \
       tests/test_google_search_tool.py \
       --import-mode=importlib
```

### 6.2 テスト一覧

| テストファイル | テスト数 | 対象ツール | グループ |
|---|---|---|---|
| `extract_full_address_tool/test_extract.py` | 20 | extract_full_address_tool | 1 |
| `.claude/skills/extract_full_address_skill/test_skill.py` | 26 | extract_full_address_skill | 1 |
| `compare_address_full_tool/test_compare_address_full.py` | 60 | compare_address_full_tool | 1 |
| `compare_address_tool/tests/test_compare_address.py` | 25 | compare_address_tool（旧版） | 1 |
| `playwright_download_tool/test_extract.py` | 19 | playwright_download_tool | 1 |
| `tests/test_google_search_mcp.py` | 14 | google_search_mcp | 2 |
| `tests/test_google_search_tool.py` | 20 | google_search_tool | 2 |
| **合計** | **184** | | |

### 6.3 テスト全実行（一括）

```bash
# グループ1
pytest extract_full_address_tool/ compare_address_full_tool/ \
       compare_address_tool/ playwright_download_tool/ \
       .claude/skills/extract_full_address_skill/

# グループ2
pytest tests/ --import-mode=importlib
```

---

## 7. アーカイブ済みツール

| ディレクトリ | 説明 |
|---|---|
| `archive/extract_address_tool/` | 旧版住所抽出ツール（市区町村レベルのみ） |
| `archive/extract_address_skill/` | 旧版スキル |
| `archive/google_search_mcp/` | MCP サーバー（未使用のためアーカイブ） |
| `archive/google_search_skill/` | Google検索スキル（`google_search_tool` CLI に一本化） |

> v6では `extract_address_tool`（市区町村レベル）を手順2-Bで使用するが、
> これは `archive/` 内ではなく `extract_address_tool/` に配置されている旧版ツール。

---

## 8. バージョン履歴

| バージョン | 日付 | 主な変更 |
|---|---|---|
| v6.0 | 2026-02-28 | 手順2を2段階化、検索クエリを市区町村レベルに変更 |
| v5.0 | 2026-02-27 | criteria.txt による公式サイト判定（手順7）追加 |
| v4.0 | 2026-01-03 | Claude API直接呼び出し廃止、サブエージェント方式に変更 |
| v1〜v3 | 2025 | 初期実装〜基本ワークフロー |

詳細仕様は `officialsitefinder_skills_v6.md` 参照。
