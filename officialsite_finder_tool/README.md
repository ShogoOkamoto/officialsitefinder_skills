# Official Site Finder Tool

施設の公式サイトのトップページを自動で発見するツールです。

## 概要

このツールは、施設名と住所を入力として、以下の処理を行います：

1. **住所抽出**: 入力された住所から都道府県・市区町村を抽出
2. **Google検索**: 施設名と住所でGoogle検索を実行
3. **HTMLダウンロード**: 検索結果のURLからHTMLをダウンロード（タイトルも取得）
4. **住所抽出**: HTMLから住所を抽出
5. **住所照合**: 抽出した住所と入力住所を照合（参考情報として記録）
6. **コンテンツ判定**: `judge_officialsite_content_skill` で公式トップページか判定（住所照合結果に関わらず全URLに適用）
7. **公式サイト判定** (オプション): criteria.txtの基準でURLが収集対象かをサブエージェントで判定

## 特徴

- **精度向上** (v6): 住所照合の有無に関わらず全URLをコンテンツ判定し、住所抽出できない場合でも公式サイトを発見可能
- **精度向上** (v5): criteria.txtの判定基準によりポータルサイト等を自動除外
- **APIコスト削減**: Claude APIを直接呼び出す代わりに、Claude Codeのサブエージェント機能を活用
- **自動化**: 複数のツールを組み合わせて完全自動化

## 必要な環境

### 依存ツール

以下のツールが同じプロジェクト内に存在する必要があります：

1. **extract_full_address_tool**: 日本語住所抽出ツール
2. **google_search_tool**: Google Custom Search APIツール
3. **playwright_download_tool**: HTMLダウンロードツール（タイトル取得対応）
4. **compare_address_tool**: 住所比較ツール

### 環境変数

`.env`ファイルに以下を設定：

```env
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
```

### criteria.txt（オプション）

プロジェクトルートに `criteria.txt` を配置することで、コンテンツ判定Yes後にさらに収集対象か否かの判定が有効になります。
ファイルが存在しない場合はコンテンツ判定Yesで即成功となります。

## 使い方

### 基本的な使い方

```bash
python -m officialsite_finder_tool --name "施設名" --address "住所"
```

### 例: 東京タワー

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
```

### criteria.txtのパスを指定

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8" \
  --criteria-file "/path/to/criteria.txt"
```

### Claude Codeスキルとして使用

Claude Codeでスキルとして使用する場合：

```
/officialsite-finder
```

Claude Codeが自動的に施設名と住所を尋ね、処理を実行します。

## コマンドライン引数

| 引数 | 説明 | 必須 |
|------|------|------|
| `--name` | 施設名 | ✓ |
| `--address` | 施設住所 | ✓ |
| `--criteria-file` | criteria.txtのパス（デフォルト: プロジェクトルート） | - |
| `--content-judgment` | コンテンツ判定結果（Yes/No） | - |
| `--content-pending-url` | コンテンツ判定対象のURL | - |
| `--criteria-judgment` | 公式サイト判定結果（eligible/not_eligible） | - |
| `--criteria-pending-url` | 公式サイト判定対象のURL | - |
| `--matched-address` | 住所照合で一致した住所（判定結果返却時に渡す） | - |
| `--skip-urls` | スキップするURLのJSON配列 | - |
| `--search-results` | 前回の検索結果JSON配列（Google検索を再実行しない） | - |
| `--target-address` | 抽出済みターゲット住所（住所抽出を再実行しない） | - |

## 出力形式

### 成功時

```json
{
  "success": true,
  "facility_name": "東京タワー",
  "input_address": "東京都港区芝公園4-2-8",
  "official_site_url": "https://www.tokyotower.co.jp/",
  "matched_address": "東京都港区",
  "message": "公式サイトのトップページを発見しました"
}
```

### コンテンツ判定依頼時（v6新規）

```json
{
  "action": "request_content_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/",
  "title": "東京タワー | Tokyo Tower",
  "html_text_preview": "【HTMLテキストの先頭5000文字】",
  "address_matched": true,
  "matched_address": "東京都港区",
  "search_results": [...],
  "target_address": "東京都港区"
}
```

### 公式サイト判定依頼時（criteria.txt使用）

```json
{
  "action": "request_criteria_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/",
  "html_text_preview": "【HTMLテキストの先頭5000文字】",
  "criteria": "【criteria.txtの全文】",
  "question": "このページは criteria.txt の「URL収集対象」に該当しますか？...",
  "matched_address": "東京都港区"
}
```

### 失敗時

```json
{
  "success": false,
  "facility_name": "施設名",
  "input_address": "住所",
  "message": "エラーメッセージ"
}
```

## サブエージェント連携の仕組み（v6）

### 1. 初回実行

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
```

ツールは検索・ダウンロード・住所照合を行い、住所照合の結果に関わらず `action: "request_content_judgment"` を出力します。

### 2. Claude Codeがサブエージェントを起動（コンテンツ判定）

Claude CodeはSKILL.mdの指示に従い、Task toolで `judge_officialsite_content_skill` を使うサブエージェントを起動：

```
施設名: 東京タワー
URL: https://www.tokyotower.co.jp/
タイトル: 東京タワー | Tokyo Tower
ページテキスト: ...
参考情報: 住所照合結果 = True
```

### 3. 判定結果を受け取り

サブエージェントが "Yes"（公式トップページ）または "No" を返します。

### 4a. Yes の場合 → 判定結果で再実行

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8" \
  --content-judgment "Yes" \
  --content-pending-url "https://www.tokyotower.co.jp/" \
  --matched-address "東京都港区"
```

→ criteria.txtがあればcriteria判定へ、なければ成功

### 4b. No の場合 → 次のURLへ

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8" \
  --content-judgment "No" \
  --content-pending-url "https://tabelog.com/..." \
  --search-results '[...検索結果...]' \
  --target-address "東京都港区" \
  --skip-urls '["https://tabelog.com/..."]'
```

→ スキップリストに追加して次のURLを処理

## 処理フロー詳細

```
1. 入力検証
   ↓
2. 住所抽出 (extract_full_address_tool)
   ↓
3. Google検索 (google_search_tool)
   ↓
4-6. URLループ処理:
   4. HTMLダウンロード + タイトル取得 (playwright_download_tool)
   5. 住所抽出 (extract_full_address_tool)
   6a. 住所照合 (compare_address_tool) → 結果を記録（スキップしない）
   6b. コンテンツ判定依頼 (judge_officialsite_content_skill) ← v6新規
       - Yes → 手順7または成功
       - No  → skip_urlsに追加して次のURLへ
   ↓ (Yes)
7. 公式サイト判定 (criteria.txt使用) ← オプション
   - eligible → 成功
   - not_eligible → 次のURLへ (skip-urlsに追加)
   ↓ (eligible or criteria.txtなし)
8. 成功
```

## 制限事項

- **日本語住所のみ**: 現在は日本の住所にのみ対応
- **検索結果上位5件**: Google検索結果の上位5件のみをチェック
- **処理時間**: 2-5分程度かかる場合があります
- **API制限**: Google Custom Search APIの制限に依存

## トラブルシューティング

### 環境変数エラー

```
Error: GOOGLE_API_KEY and GOOGLE_CSE_ID must be set
```

→ `.env`ファイルにAPIキーとCSE IDを設定してください。

### criteria.txt が見つからない

```
[WARNING] criteria.txt not found at criteria.txt - criteria judgment will be skipped
```

→ プロジェクトルートに `criteria.txt` を配置するか、`--criteria-file` でパスを指定してください。
criteria.txtなしでも動作します（コンテンツ判定Yesで即成功）。

### 住所抽出エラー

```
住所の抽出に失敗しました
```

→ 入力住所に都道府県と市区町村が含まれているか確認してください。

### 検索結果0件

```
検索結果が見つかりませんでした
```

→ 施設名が正確か確認してください。また、住所を変更してみてください。

## 開発者向け情報

### ディレクトリ構造

```
officialsite_finder_tool/
├── __init__.py          # モジュール初期化
├── __main__.py          # メインスクリプト（v6対応）
└── README.md            # このファイル
```

### テスト

```bash
# ヘルプメッセージの確認
python -m officialsite_finder_tool --help

# 依存ツールの確認
python -m extract_full_address_tool.extract --help
python -m google_search_tool --help
python -m compare_address_tool --help
```

### ログ

ツールは標準エラー出力にログを出力します：

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8" 2>&1 | tee log.txt
```

## ライセンス

MIT License

## 関連ドキュメント

- [SKILL.md](../.claude/skills/officialsite_finder_skill/SKILL.md): Claude Codeスキルの説明
- [judge_officialsite_content_skill](../.claude/skills/judge_officialsite_content_skill/SKILL.md): コンテンツ判定スキル
- [criteria.txt](../criteria.txt): 公式サイト判定基準
- [google_search_tool](../google_search_tool/): Google検索ツール
- [extract_full_address_tool](../extract_full_address_tool/): 住所抽出ツール
- [compare_address_tool](../compare_address_tool/): 住所比較ツール
- [playwright_download_tool](../playwright_download_tool/): HTMLダウンロードツール
