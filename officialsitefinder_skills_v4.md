# 施設公式サイト発見スキル 仕様書 v4

## 概要

施設名称と住所を入力として、Google検索と住所照合により施設の公式サイトのトップページを自動発見するスキルです。

## v4の主な変更点

- **Claude API呼び出しを削除**: 手順7のLLM判定でClaude APIを直接呼び出す代わりに、Claude Codeのサブエージェント機能を活用
- **実装の簡略化**: APIキー管理（Google除く）やClaude APIへのHTTPリクエスト処理が不要に
- **コスト削減**: Claude API呼び出しコストが不要
- **判定依頼レスポンス形式の追加**: `action: "request_judgment"` 形式でClaude Codeに判定を依頼
- **環境変数の削減**: `ANTHROPIC_API_KEY` が不要に（`GOOGLE_API_KEY`と`GOOGLE_CSE_ID`のみ必要）

## 入力データ

1. **施設名称** (必須): 検索対象となる施設の名称
2. **施設の住所** (必須): 施設の所在地（都道府県〜市区町村以上を含むこと）

### 入力検証

- 両方のフィールドが必須
- 空文字列や空白のみの入力はエラー
- バリデーションエラー時は以下のJSON形式でエラーを返す：
  ```json
  {
    "success": false,
    "facility_name": "",
    "input_address": "",
    "message": "入力エラー: 施設名称と住所は必須です"
  }
  ```

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

### 失敗時

```json
{
  "success": false,
  "facility_name": "施設名",
  "input_address": "入力された住所",
  "message": "公式サイトが見つかりませんでした"
}
```

### 判定依頼時（v4新規）

トップページ判定が必要な場合、以下の形式でClaude Codeに判定を依頼：

```json
{
  "action": "request_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/about",
  "html_text_preview": "【先頭5000文字のHTMLテキスト】",
  "question": "このページは「東京タワー」の公式サイトのトップページですか？YesまたはNoで答えてください。",
  "matched_address": "東京都港区"
}
```

Claude Codeはこの出力を検知し、サブエージェントを起動して判定を行い、結果をツールに返します。

## 処理フロー

### 手順1: 入力データの検証

- 施設名称と住所が両方とも入力されているか確認
- 入力が不正な場合はエラーを返して終了

### 手順2: 住所から都道府県・市区町村を抽出

- **使用ツール**: `extract_address_tool`
- **処理内容**: 入力された施設住所から都道府県〜市区町村レベルの住所を抽出
  - 抽出レベル: 都道府県 + 市区町村（例: 「東京都港区」「北海道札幌市」）
  - 丁目・番地・建物名は抽出されない
- **実行方法**: `python -m extract_address_tool.extract`
- **エラー処理**: 住所が抽出できなかった場合（空配列が返された場合）はエラーを返して終了

### 手順3: Google検索で公式サイト候補を取得

- **使用ツール**: `google_search_tool`
- **検索クエリ構成**: `{施設名称} {都道府県市区町村}`
  - 例: 「東京タワー 東京都港区」
  - シンプルな形式でGoogle Custom Searchの関連度アルゴリズムを活用
- **取得件数**: 最大5件
- **実行方法**: `python -m google_search_tool "query" -n 5`
- **フィルタリング**:
  - PDFファイル（`.pdf`で終わるURL）はスキップ
  - （オプション）SNS（twitter.com、facebook.com）や口コミサイト（tabelog.com、google.com/maps）の除外も検討可
- **エラー処理**:
  - 検索結果が0件の場合: `{"results": [], "count": 0}` が返される → エラーを返して終了
  - API エラー時: エラーメッセージを返して終了

### 手順4: 各URLのHTMLをダウンロード

- **使用ツール**: `playwright_download_tool`
- **処理内容**: 検索結果のURLを上から順にアクセスし、プレーンテキストを取得
- **実行方法**: `python download.py {URL} --format=text`
- **処理順序**: Google検索結果の上位から順に処理（関連度が高い順）
- **エラー処理**:
  - 404エラー、タイムアウト、認証エラーなどが発生した場合
  - エラーをログに記録し、次のURLに進む
  - 5件すべてダウンロード失敗した場合はエラーを返して終了

### 手順5: HTMLテキストから住所を抽出

- **使用ツール**: `extract_address_tool`
- **処理内容**: 取得したプレーンテキストから全ての住所を抽出
- **実行方法**: `python -m extract_address_tool.extract`
- **エラー処理**:
  - 住所が抽出できなかった場合（空配列 `[]` が返された場合）
  - 住所情報がないページ（お問い合わせページ、ニュース記事など）と判断
  - 次のURLに進む

### 手順6: 住所の照合

- **使用ツール**: `compare_address_tool`
- **処理内容**:
  - 手順2で得られた入力値の都道府県市区町村と、手順5で抽出された各住所を比較
  - マッチした場合、そのURLを候補として次の手順に進む
- **実行方法**: `python -m compare_address_tool "{住所1}" "{住所2}"`
- **比較仕様**:
  - 正規化: 全角→半角、空白除去、小文字化（NFKC normalization）
  - 比較方法: 正規化後の完全一致
  - 表記ゆれ: 全角半角・空白の違いは自動吸収
- **注意事項**: 「東京都」と「東京」は不一致と判定されるため、統一した形式を使用
- **複数マッチ時の処理**:
  - 最初にマッチしたURLのみを採用
  - Google検索結果は関連度順のため、最初にマッチしたものが最も適切
- **エラー処理**:
  - 5件すべてで住所がマッチしなかった場合
  - 「該当する公式サイトが見つかりませんでした」としてエラーを返して終了

### 手順7: トップページ判定（ハイブリッド方式 - サブエージェント版）

住所がマッチしたURLについて、それが施設のトップページか否かを判定します。

#### 第1段階: URL構造による判定

以下のいずれかに該当する場合、トップページと判定：
- ドメイン直下（例: `https://example.com/`, `https://example.com/index.html`）
- パスの深さが浅い（スラッシュが2個以下）

→ トップページと判定された場合は**手順10へ**

#### 第2段階: Claude Codeサブエージェントによる判定（v4の核心）

URL構造で判定できない場合、Claude Codeのサブエージェント機能を使って判定します。

##### 実装方法: サブエージェント連携

**v3からの変更点：Claude APIを直接呼び出す代わりに、Claude Code自身がサブエージェントを起動して判定を行います。**

**処理フロー：**

1. **ツールが判定依頼レスポンスを出力**:
   ```json
   {
     "action": "request_judgment",
     "facility_name": "東京タワー",
     "url": "https://www.tokyotower.co.jp/about",
     "html_text_preview": "【先頭5000文字のHTMLテキスト】",
     "question": "このページは「東京タワー」の公式サイトのトップページですか？YesまたはNoで答えてください。",
     "matched_address": "東京都港区"
   }
   ```

2. **Claude CodeがこのレスポンスをパースしてTask toolを起動**:
   ```python
   Task(
     subagent_type="general-purpose",
     description="トップページ判定",
     prompt=f"""以下のHTMLテキストが「{facility_name}」の公式サイトのトップページか判定してください。

URL: {url}

HTMLテキスト:
{html_text_preview}

トップページの場合は 'Yes'、そうでない場合は 'No' で答えてください。

判定基準:
- ページタイトルが施設名と一致するか
- トップページらしいナビゲーション構造があるか
- 「ホーム」「トップ」「Home」などの表記があるか
- コンテンツが施設全体の紹介・概要になっているか
- 特定のサービスや商品だけのページでないか

Answer: """
   )
   ```

3. **サブエージェントが判定を実行**:
   - HTMLテキストを分析
   - トップページの特徴を確認
   - "Yes" または "No" で回答

4. **Claude Codeが判定結果を取得**:
   - サブエージェントから "Yes" または "No" を受け取る

5. **Claude Codeがツールを再実行**:
   ```bash
   python -m officialsite_finder_tool \
     --name "東京タワー" \
     --address "東京都港区芝公園4-2-8" \
     --judgment "Yes" \
     --pending-url "https://www.tokyotower.co.jp/about"
   ```

6. **ツールが判定結果を処理**:
   - `--judgment "Yes"` の場合 → **手順10へ**（成功）
   - `--judgment "No"` の場合 → **手順8へ**（ドメインルート探索）

##### サブエージェント判定の利点

- **APIコスト削減**: Claude APIの直接呼び出しが不要
- **実装の簡素化**: HTTPリクエストやAPIキー管理が不要
- **統合性**: Claude Codeの既存機能を活用
- **コンテキスト保持**: メインの会話コンテキストを消費しない

##### HTMLテキストの切り詰め

- **先頭5000文字のみ**を判定に使用
- **根拠**:
  - トップページの重要情報（タイトル、ヘッダー、メインコンテンツ）は通常先頭に配置される
  - 5000文字は約1000トークンに相当（日本語の場合）
  - コンテキスト使用量の最適化

### 手順8: トップページURLの発見

現在のURLがトップページでない場合、トップページを探索します。

#### 探索方法

1. **ドメインルートに遷移**:
   - `https://example.com/path/to/page` → `https://example.com/`
   - playwright_download_toolでHTMLをダウンロード

2. **再度トップページ判定**:
   - 手順7の判定ロジックを実行（URL構造チェック → 必要に応じてサブエージェント判定）
   - トップページと判定されれば**手順10へ**

3. **HTMLメタタグからの抽出**（オプション）:
   - それでもトップページでない場合
   - HTMLから `<link rel="home">` や `<meta property="og:url">` を抽出
   - 抽出できたURLに対して手順4〜7を再実行

#### 繰り返し回数

- 最大3回までトップページ検索を試行
- **カウント対象**:
  1. 初回のトップページ判定（手順7）
  2. ドメインルートへの遷移後の判定（手順8-1, 8-2）
  3. メタタグから抽出したURLの判定（手順8-3）
- **注意**: 手順8-3で新しいURLに対して手順4〜7を再実行する場合も1回とカウント
- 3回試行してもトップページが見つからなかった場合は**手順9へ**

### 手順9: 結果なしで終了

以下のいずれかの場合、結果なしで終了：
- トップページが見つからなかった
- 検索結果が0件だった
- すべてのURLで住所がマッチしなかった
- すべてのURLでダウンロードに失敗した

```json
{
  "success": false,
  "facility_name": "施設名",
  "input_address": "入力された住所",
  "message": "公式サイトが見つかりませんでした（具体的な理由）"
}
```

### 手順10: 成功レスポンスを返す

トップページが発見された場合、成功レスポンスを返して終了：

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

## 使用ツール一覧

### 1. extract_address_tool
- **場所**: `extract_address_tool/`
- **機能**: 日本語テキストから都道府県〜市区町村レベルの住所を抽出してJSON形式で返す
- **実行方法**: `python -m extract_address_tool.extract`
- **出力形式**: JSON配列（例: `["東京都港区", "大阪府大阪市"]`）

### 2. google_search_tool
- **場所**: `google_search_tool/`
- **機能**: Google Custom Search APIで検索、JSON形式で結果を返す
- **実行方法**: `python -m google_search_tool "query" [-n 5]`
- **出力形式**:
  ```json
  {
    "results": [
      {"title": "...", "link": "https://...", "snippet": "..."}
    ],
    "count": 1
  }
  ```
- **環境変数**: `GOOGLE_API_KEY`, `GOOGLE_CSE_ID` が必要

### 3. playwright_download_tool
- **場所**: `playwright_download_tool/`
- **機能**: PlaywrightでHTMLダウンロード、BeautifulSoupでプレーンテキスト抽出
- **実行方法**: `python download.py <URL> [--format=text|html]`
- **出力形式**: 標準出力にプレーンテキストまたはHTML

### 4. compare_address_tool
- **場所**: `compare_address_tool/`
- **機能**: 日本語住所を正規化（全角半角、空白除去）して比較
- **実行方法**:
  - **CLI使用時**: `python -m compare_address_tool <address1> <address2>`
  - **Python使用時**: `from compare_address_tool import compare_addresses`
- **出力**:
  - **CLI使用時**: 一致する場合は終了コード0、一致しない場合は終了コード1
  - **Python使用時**: `compare_addresses(addr1, addr2)` が `True`/`False` を返す

### 5. officialsite_finder_tool（メインツール）
- **場所**: `officialsite_finder_tool/`
- **機能**: 上記4つのツールを統合し、公式サイトのトップページを発見
- **実行方法**:
  ```bash
  # 初回実行
  python -m officialsite_finder_tool --name "施設名" --address "住所"

  # 判定結果付き実行
  python -m officialsite_finder_tool --name "施設名" --address "住所" \
    --judgment "Yes|No" --pending-url "URL"
  ```
- **出力形式**: JSON（成功、失敗、または判定依頼）

## Claude Codeスキルとしての実装

### SKILL.md

場所: `.claude/skills/officialsite_finder_skill/SKILL.md`

スキル定義ファイルには以下を記載：
- スキルの説明と使用タイミング
- 入力要件（施設名、住所）
- サブエージェント起動の手順
- 判定依頼レスポンスの処理方法

### 実行フロー

1. **ユーザーがスキルを起動**:
   ```
   /officialsite-finder
   ```

2. **Claude Codeが施設名と住所を尋ねる**

3. **Claude Codeがツールを実行**:
   ```bash
   python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
   ```

4. **ツールが判定依頼を出力した場合**:
   ```json
   {
     "action": "request_judgment",
     "facility_name": "東京タワー",
     "url": "https://...",
     "html_text_preview": "...",
     "question": "..."
   }
   ```

5. **Claude CodeがTask toolでサブエージェントを起動**

6. **サブエージェントが判定結果を返す**（"Yes" または "No"）

7. **Claude Codeが判定結果でツールを再実行**:
   ```bash
   python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8" \
     --judgment "Yes" --pending-url "https://..."
   ```

8. **ツールが最終結果を出力**（成功または失敗）

9. **Claude Codeがユーザーに結果を報告**

## エラーハンドリング詳細

### タイムアウト設定

- **HTMLダウンロード**: 30秒（playwright_download_toolのデフォルト）
- **Google検索API**: 30秒（google_search_toolのデフォルト）
- **サブエージェント判定**: 60秒（Claude Codeのサブエージェント応答待ち）
- **全体処理**: 10分（全ての処理を含む）
  - **根拠**:
    - Google検索: 30秒
    - HTMLダウンロード×5件: 30秒×5 = 150秒
    - 住所抽出・比較: 各10秒×5 = 50秒
    - サブエージェント判定×3回: 60秒×3 = 180秒
    - バッファ: 30秒
    - **合計**: 約440秒 ≈ 7.5分（余裕を持たせて10分）

### ログ出力

以下のタイミングでログを出力（推奨）：
- 各手順の開始時・終了時
- エラー発生時（詳細なエラー情報を含む）
- 住所マッチ成功時
- トップページ発見時
- サブエージェント判定依頼時と結果受信時

ログレベル：
- **INFO**: 正常な処理の進行状況
- **WARNING**: 単一URLの処理失敗（次のURLに進む場合）
- **ERROR**: スキル全体の処理失敗

#### ログフォーマット例

```
2026-01-03 12:34:56 [INFO] 手順1: 入力データの検証を開始
2026-01-03 12:34:56 [INFO] 手順2: 住所抽出を開始 - 入力: "東京都港区芝公園4-2-8"
2026-01-03 12:34:56 [INFO] 手順2: 住所抽出完了 - 結果: "東京都港区"
2026-01-03 12:34:57 [INFO] 手順3: Google検索開始 - クエリ: "東京タワー 東京都港区"
2026-01-03 12:34:58 [INFO] 手順3: 検索完了 - 結果件数: 5
2026-01-03 12:34:58 [INFO] 手順4: HTMLダウンロード開始 - URL: "https://example.com"
2026-01-03 12:35:00 [WARNING] 手順4: HTMLダウンロード失敗 - URL: "https://example.com" - エラー: 404 Not Found
2026-01-03 12:35:00 [INFO] 手順6: 住所マッチ成功 - URL: "https://www.tokyotower.co.jp/about"
2026-01-03 12:35:01 [INFO] 手順7: サブエージェント判定依頼 - URL: "https://www.tokyotower.co.jp/about"
2026-01-03 12:35:15 [INFO] 手順7: 判定結果受信 - 結果: No
2026-01-03 12:35:15 [INFO] 手順8: ドメインルートへ遷移 - URL: "https://www.tokyotower.co.jp/"
2026-01-03 12:35:20 [INFO] 手順7: トップページ判定 - 結果: Yes (URL構造判定)
2026-01-03 12:35:20 [INFO] 手順10: 成功 - 公式サイト発見: "https://www.tokyotower.co.jp/"
```

### リトライポリシー

- **ネットワークエラー**: リトライせず次のURLに進む
- **タイムアウト**: リトライせず次のURLに進む
- **Google Search API エラー**: リトライせず処理を終了
- **一時的なエラー**: 同一URLに対するリトライは行わない（検索結果の次のURLを試行）
- **サブエージェント判定エラー**: 不明な回答の場合は次のURLに進む

### 中間結果の保存（オプション）

デバッグやトラブルシューティングのため、以下の中間結果を保存することを推奨：

- **保存内容**:
  - ダウンロードしたHTML（各URL）
  - 抽出した住所（各URL）
  - サブエージェント判定依頼内容と結果
  - 検索クエリと結果
- **保存先**: `./debug/{facility_name}_{timestamp}/`
  - 例: `./debug/東京タワー_20260103_123456/`
- **ファイル構成**:
  ```
  ./debug/東京タワー_20260103_123456/
  ├── 00_search_query.txt
  ├── 01_search_results.json
  ├── 02_url1_html.txt
  ├── 02_url1_addresses.json
  ├── 03_url2_html.txt
  ├── 03_url2_addresses.json
  ├── 04_subagent_request.json
  └── 04_subagent_response.json
  ```
- **本番環境**: 環境変数 `DEBUG_MODE=false` で無効化可能

## 実装に関する注意事項

### 住所形式の統一

- extract_address_toolは都道府県〜市区町村レベルまで抽出
- compare_address_toolは完全一致判定
- 「東京都渋谷区」と「東京」は不一致と判定される
- 入力住所と抽出住所の形式を統一すること

### Google検索の最適化

- クエリはシンプルに保つ（施設名 + 住所）
- Google Custom Searchの関連度アルゴリズムを信頼
- 不要なキーワードを追加しない

### サブエージェント判定の最適化

- **HTMLテキストの切り詰め**: 先頭5000文字のみを使用
  - **根拠**:
    - トップページの重要情報（タイトル、ヘッダー、メインコンテンツ）は通常先頭に配置される
    - 5000文字は約1000トークンに相当（日本語の場合）
- **判定依頼の形式**: シンプルで明確な質問形式
- **回答形式**: Yes/No の明確な回答を求める
- **判定基準の明示**: サブエージェントに判定基準を明示的に伝える

### サブエージェント連携の実装詳細

**ツール側の実装**:

```python
# 判定依頼を標準出力にJSON形式で出力
judgment_request = {
    "action": "request_judgment",
    "facility_name": facility_name,
    "url": url,
    "html_text_preview": html_text[:5000],
    "question": f"このページは「{facility_name}」の公式サイトのトップページですか？YesまたはNoで答えてください。",
    "matched_address": matched_address
}
print(json.dumps(judgment_request, ensure_ascii=False))
sys.exit(0)  # 判定待ちのため一旦終了
```

**Claude Code側の処理**（SKILL.mdに記載）:

```python
# 1. ツールの出力をパース
output = json.loads(tool_output)
if output.get("action") == "request_judgment":
    # 2. Task toolでサブエージェントを起動
    result = Task(
        subagent_type="general-purpose",
        description="トップページ判定",
        prompt=f"""以下のHTMLテキストが「{output['facility_name']}」の公式サイトのトップページか判定してください。

URL: {output['url']}

HTMLテキスト:
{output['html_text_preview']}

{output['question']}

判定基準:
- ページタイトルが施設名と一致するか
- トップページらしいナビゲーション構造があるか
- 「ホーム」「トップ」「Home」などの表記があるか
- コンテンツが施設全体の紹介・概要になっているか

Answer: """
    )

    # 3. 判定結果を取得（"Yes" or "No"）
    judgment = result.strip()

    # 4. ツールを再実行
    run_tool(
        f"python -m officialsite_finder_tool "
        f"--name '{output['facility_name']}' "
        f"--address '{original_address}' "
        f"--judgment '{judgment}' "
        f"--pending-url '{output['url']}'"
    )
```

### パフォーマンス考慮

- 並列処理は行わず、順次処理を推奨
- 最初にマッチしたURLで処理を終了するため、平均的には1-2件のURL処理で完了
- 最悪ケースでも5件のURL処理で完了
- サブエージェント判定は必要な場合のみ実行（URL構造で判定可能な場合はスキップ）

## テスト計画

### 単体テスト

各ツールの動作確認：
- extract_address_tool: 様々な形式の住所からの抽出
- google_search_tool: 検索クエリと結果の取得
- playwright_download_tool: HTMLダウンロードとテキスト抽出
- compare_address_tool: 正規化と比較ロジック

### 統合テスト

エンドツーエンドのフロー確認：
- 正常系: 公式サイトが正しく発見される
- 異常系: 検索結果0件、住所不一致など
- サブエージェント判定: 正しく判定依頼が行われ、結果が処理されるか

### サブエージェント判定テスト

- トップページのHTMLで "Yes" が返されるか
- サブページのHTMLで "No" が返されるか
- 判定結果が正しくツールに渡されるか
- 判定結果に基づいて適切な処理が行われるか

### エッジケーステスト

- 施設名が一般的すぎる場合（例: 「市役所」）
- 住所が不完全な場合
- HTMLに住所が複数含まれる場合
- トップページでないページがヒットした場合
- サブエージェント判定で不明な回答が返された場合
- ドメインルートもトップページでない場合

## 環境要件

### 必須環境変数

```env
# Google Custom Search API
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
```

### 不要になった環境変数（v3から削除）

- `ANTHROPIC_API_KEY`: Claude API呼び出しが不要になったため削除

### Pythonパッケージ

- Python 3.8以上
- 各ツールの依存パッケージ（requirements.txtまたはpyproject.toml参照）

## デプロイメント

### Claude Codeスキルとしてのインストール

1. **スキル定義の配置**:
   ```
   .claude/skills/officialsite_finder_skill/SKILL.md
   ```

2. **ツールの配置**:
   ```
   officialsite_finder_tool/__init__.py
   officialsite_finder_tool/__main__.py
   ```

3. **依存ツールの確認**:
   - extract_address_tool
   - google_search_tool
   - playwright_download_tool
   - compare_address_tool

4. **環境変数の設定**:
   - プロジェクトルートに`.env`ファイルを作成
   - `GOOGLE_API_KEY`と`GOOGLE_CSE_ID`を設定

5. **動作確認**:
   ```bash
   python -m officialsite_finder_tool --help
   ```

## バージョン履歴

### v4.0 (2026-01-03)

**主要変更:**
- **Claude API呼び出しを削除**: Claude Code自身がサブエージェントを起動して判定を行う方式に変更
- **サブエージェント連携の実装**: Task toolを使ったサブエージェント起動フローを追加
- **判定依頼レスポンス形式を追加**: `action: "request_judgment"` 形式を導入
- **環境変数の削減**: `ANTHROPIC_API_KEY` が不要に（`GOOGLE_API_KEY`と`GOOGLE_CSE_ID`のみ）
- **タイムアウト設定を更新**: サブエージェント判定を60秒、全体を10分に変更
- **ログ出力を更新**: サブエージェント判定依頼と結果受信のログを追加
- **実装ガイドラインを追加**: Claude Codeスキルとしての実装方法を詳細化
- **コスト最適化**: Claude API呼び出しコストが完全に不要に

**技術的改善:**
- API依存の削減
- 実装の簡素化（HTTPリクエスト処理不要）
- Claude Codeエコシステムとの統合性向上
- デバッグの容易性向上（サブエージェントのログが確認可能）

**互換性:**
- 出力形式（成功・失敗レスポンス）はv3と互換
- 新たに判定依頼レスポンス形式を追加
- ツールのコマンドライン引数に`--judgment`と`--pending-url`を追加

### v3.0 (2026-01-03)

- LLM判定の実装詳細を追加（Claude API呼び出し方法、レスポンス解析）
- compare_address_toolの出力形式を明確化（CLI vs Python使用時）
- HTMLテキスト切り詰めの根拠を追加（5000文字 = 約1000トークン）
- ループ回数カウントの詳細を追加（手順8）
- ログフォーマットの具体例を追加
- エラーレスポンスフィールドを統一（"error" → "message"）
- 全体タイムアウトの根拠を追加（内訳を明記）
- 中間結果の保存セクションを追加（デバッグ用）
- Claude APIタイムアウト設定を追加（20秒）

### v2.0 (2026-01-03)

- タイポ修正（extract_address_toool → extract_address_tool）
- 助詞の重複修正（「マッチした場合をのURL」→「マッチした場合のURL」）
- ツール名の統一（google_search_toolを使用）
- 出力形式をJSON形式で明確化
- トップページ判定をハイブリッド方式で明確化
- エラーハンドリングの詳細を追加
- 各手順の詳細仕様を追加
- 使用ツール一覧を追加
- テスト計画を追加

### v1.0

- 初版

## まとめ

v4では、Claude APIの直接呼び出しを廃止し、Claude Codeのサブエージェント機能を活用することで：

1. **コスト削減**: Claude API呼び出しコストが完全に不要
2. **実装の簡素化**: HTTPリクエスト処理やAPIキー管理（Claude用）が不要
3. **統合性の向上**: Claude Codeのエコシステムに完全統合
4. **同等の機能**: v3と同等のトップページ判定精度を維持

この変更により、より実用的で運用コストの低いシステムを実現しました。
