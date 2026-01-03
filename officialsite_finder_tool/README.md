# Official Site Finder Tool

施設の公式サイトのトップページを自動で発見するツールです。

## 概要

このツールは、施設名と住所を入力として、以下の処理を行います：

1. **住所抽出**: 入力された住所から都道府県・市区町村を抽出
2. **Google検索**: 施設名と住所でGoogle検索を実行
3. **HTMLダウンロード**: 検索結果のURLからHTMLをダウンロード
4. **住所照合**: HTMLから住所を抽出し、入力住所と照合
5. **トップページ判定**: Claude Codeのサブエージェントを使ってトップページか判定

## 特徴

- **APIコスト削減**: Claude APIを直接呼び出す代わりに、Claude Codeのサブエージェント機能を活用
- **高精度**: 住所照合により、正確な公式サイトを発見
- **自動化**: 複数のツールを組み合わせて完全自動化

## 必要な環境

### 依存ツール

以下のツールが同じプロジェクト内に存在する必要があります：

1. **extract_address_tool**: 日本語住所抽出ツール
2. **google_search_tool**: Google Custom Search APIツール
3. **playwright_download_tool**: HTMLダウンロードツール
4. **compare_address_tool**: 住所比較ツール

### 環境変数

`.env`ファイルに以下を設定：

```env
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
```

## 使い方

### 基本的な使い方

```bash
python -m officialsite_finder_tool --name "施設名" --address "住所"
```

### 例: 東京タワー

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
```

### Claude Codeスキルとして使用

Claude Codeでスキルとして使用する場合：

```
/officialsite-finder
```

Claude Codeが自動的に施設名と住所を尋ね、処理を実行します。

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

### 判定依頼時

トップページ判定が必要な場合、以下を出力します：

```json
{
  "action": "request_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/about",
  "html_text_preview": "【HTMLテキストの先頭5000文字】",
  "question": "このページは「東京タワー」の公式サイトのトップページですか？YesまたはNoで答えてください。",
  "matched_address": "東京都港区"
}
```

この場合、Claude Codeがサブエージェントを起動して判定を行い、結果を返します。

### 失敗時

```json
{
  "success": false,
  "facility_name": "施設名",
  "input_address": "住所",
  "message": "エラーメッセージ"
}
```

## サブエージェント連携の仕組み

### 1. 初回実行

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
```

ツールは検索・ダウンロード・住所照合を行い、トップページ判定が必要な場合は`action: "request_judgment"`を出力します。

### 2. Claude Codeがサブエージェントを起動

Claude CodeはSKILL.mdの指示に従い、Task toolでサブエージェントを起動：

```python
Task(
  subagent_type="general-purpose",
  description="Determine if page is top page",
  prompt="HTMLテキストを分析して、トップページか判定してください..."
)
```

### 3. 判定結果を受け取り

サブエージェントが"Yes"または"No"を返します。

### 4. 判定結果で再実行

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8" --judgment "Yes" --pending-url "https://..."
```

ツールは判定結果に基づいて処理を完了します。

## 処理フロー詳細

```
1. 入力検証
   ↓
2. 住所抽出 (extract_address_tool)
   ↓
3. Google検索 (google_search_tool)
   ↓
4-6. URLループ処理:
   4. HTMLダウンロード (playwright_download_tool)
   5. 住所抽出 (extract_address_tool)
   6. 住所照合 (compare_address_tool)
   ↓ (住所一致)
7. トップページ判定:
   - URL構造チェック → トップページなら完了
   - Claude Code判定依頼 → 判定結果待ち
   ↓ (判定結果: No)
8. ドメインルートへ遷移
   ↓
再度7へ (最大3回)
   ↓
9. 失敗 or 10. 成功
```

## 制限事項

- **日本語住所のみ**: 現在は日本の住所にのみ対応
- **検索結果上位5件**: Google検索結果の上位5件のみをチェック
- **処理時間**: 1-3分程度かかる場合があります
- **API制限**: Google Custom Search APIの制限に依存

## トラブルシューティング

### 環境変数エラー

```
Error: GOOGLE_API_KEY and GOOGLE_CSE_ID must be set
```

→ `.env`ファイルにAPIキーとCSE IDを設定してください。

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

### HTMLダウンロード失敗

```
[WARNING] Failed to download HTML from ...
```

→ ネットワーク接続を確認してください。または、そのURLがアクセス制限されている可能性があります。

## 開発者向け情報

### ディレクトリ構造

```
officialsite_finder_tool/
├── __init__.py          # モジュール初期化
├── __main__.py          # メインスクリプト
└── README.md            # このファイル
```

### テスト

```bash
# ヘルプメッセージの確認
python -m officialsite_finder_tool --help

# 依存ツールの確認
python -m extract_address_tool.extract --help
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
- [officialsitefinder_skills_v3.md](../officialsitefinder_skills_v3.md): 詳細な仕様書（v3）
- [google_search_tool](../google_search_tool/): Google検索ツール
- [extract_address_tool](../extract_address_tool/): 住所抽出ツール
- [compare_address_tool](../compare_address_tool/): 住所比較ツール
- [playwright_download_tool](../playwright_download_tool/): HTMLダウンロードツール
