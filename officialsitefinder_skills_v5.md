# 施設公式サイト発見スキル 仕様書 v5

## 概要

施設名称と住所を入力として、Google検索と住所照合により施設の公式サイトのトップページを自動発見するスキルです。

## v5の主な変更点

- **公式サイト判定ステップの追加（手順7）**: 住所マッチ後に `criteria.txt` の基準に基づき「このURLは収集対象か」をサブエージェントが判定する手順を追加
- **既存の手順7〜10 → 手順8〜11 に繰り下げ**
- **新しい判定依頼レスポンス形式 `action: "request_criteria_judgment"` を追加**
- **新しいツール引数 `--criteria-judgment` と `--criteria-pending-url` を追加**
- **`--criteria-file` オプションを追加**: criteria.txtのパスを指定可能（デフォルト: プロジェクトルートの `criteria.txt`）

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
  "message": ["(公式サイトと判定した理由1)", "(公式サイトと判定した理由2)"]
}
```

### 失敗時

```json
{
  "success": false,
  "facility_name": "施設名",
  "input_address": "入力された住所",
  "message": ["(公式サイトと判定なかった理由)"]
}
```

### 公式サイト判定依頼時（新規追加）

公式サイト判定が必要な場合、以下の形式でClaude Codeに判定を依頼：

```json
{
  "action": "request_criteria_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/about",
  "html_text_preview": "【先頭5000文字のHTMLテキスト】",
  "criteria": "【criteria.txtの全文】",
  "question": "このページは criteria.txt の「URL収集対象」に該当しますか？「eligible」（収集対象）または「not_eligible」（収集対象外）で回答し、理由を1行で添えてください。",
  "matched_address": "東京都港区"
}
```

### トップページ判定依頼時（v4から継続）

トップページ判定が必要な場合、以下の形式でClaude Codeに判定を依頼：

```json
{
  "action": "request_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/about",
  "html_text_preview": "【先頭5000文字のHTMLテキスト】",
  "question": "このページは「東京タワー」の公式サイトのトップページですか？YesまたはNoで答えてください。また、そう判断した根拠を記述してください。",
  "matched_address": "東京都港区"
}
```

Claude Codeはこれらの出力を検知し、サブエージェントを起動して判定を行い、結果をツールに返します。

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

### 手順7: 公式サイト判定（criteria.txt使用）← v5新規追加

住所がマッチしたURLについて、`criteria.txt` の基準を使ってそのURLが収集対象の公式サイトか否かを判定します。

#### criteria.txtの読み込み

- ツール起動時に `criteria.txt` を読み込む
- デフォルトパス: プロジェクトルートの `criteria.txt`
- `--criteria-file` オプションで上書き可能

#### 処理フロー

1. **ツールが判定依頼レスポンスを出力**:
   ```json
   {
     "action": "request_criteria_judgment",
     "facility_name": "東京タワー",
     "url": "https://www.tokyotower.co.jp/about",
     "html_text_preview": "【先頭5000文字のHTMLテキスト】",
     "criteria": "【criteria.txtの全文】",
     "question": "このページは criteria.txt の「URL収集対象」に該当しますか？「eligible」（収集対象）または「not_eligible」（収集対象外）で回答し、理由を列挙して添えてください。",
     "matched_address": "東京都港区"
   }
   ```

2. **Claude CodeがこのレスポンスをパースしてTask toolを起動**:
   ```python
   Task(
     subagent_type="general-purpose",
     description="公式サイト判定",
     prompt=f"""以下のページが「{facility_name}」の公式サイトとして収集対象か判定してください。

URL: {url}

HTMLテキスト:
{html_text_preview}

判定基準:
{criteria}

「eligible」（収集対象）または「not_eligible」（収集対象外）で回答し、理由を列挙して添えてください。

Answer: """
   )
   ```

3. **サブエージェントが判定を実行**:
   - HTMLテキストとURLを分析
   - criteria.txtの収集対象・収集対象外の基準を確認
   - "eligible" または "not_eligible" で回答し、理由を1行で添える

4. **Claude Codeが判定結果を取得**:
   - サブエージェントから "eligible" または "not_eligible" を受け取る

5. **Claude Codeがツールを再実行**:
   ```bash
   python -m officialsite_finder_tool \
     --name "東京タワー" \
     --address "東京都港区芝公園4-2-8" \
     --criteria-judgment "eligible|not_eligible" \
     --criteria-pending-url "https://www.tokyotower.co.jp/about"
   ```

6. **ツールが判定結果を処理**:
   - `--criteria-judgment "eligible"` の場合 → **手順8へ**（トップページ判定）
   - `--criteria-judgment "not_eligible"` の場合 → 次のURLへ（5件すべてで対象外なら**手順10へ**）

#### 判定基準の概要（criteria.txtより）

**URL収集対象:**
- （１）施設単独サイトのトップページ
- （２）法人・グループサイト内の個別施設紹介ページ
- （３）法人・グループサイト内の個別アクセスページ
- （４）自治体サイト内の公営施設ページ
- （５）医師会サイト内の医師会施設ページ

以下も収集対象:
- 自由診療施設
- 工事中のページ
- PDFページ
- 介護関連施設や小児療育施設の併設診療所のうち、診療所の紹介ページがあるもの
- 詳細情報が別ページに存在するもの
- index.html、main.phpなどを末尾から除去するとアクセスできないページ
- 公式サイトが複数ある

**URL収集対象外:**
- （１）ポータルサイト
- （２）予約サイト
- （３）自治体サイト内で紹介されている、公営でない施設のページ
- （４）医師会サイト内で紹介されている、医師会営でない施設のページ
- （５）介護関連施設や小児療育施設の併設診療所のうち、診療所の紹介ページがないもの
- （６）ビルや商業施設のテナント案内のページ
- （７）ブログやSNS
- （８）訪問診療ネットワークのHP
- （９）お知らせページ
- （10）法人・グループサイトのトップページ

#### エラー処理

- criteria.txtが見つからない場合: 警告を出力し、手順7をスキップして手順8へ進む
- サブエージェント判定でエラーが発生した場合: 不明な回答の場合は次のURLに進む
- サブエージェント判定で不明確な回答が返された場合: 次のURLに進む

### 手順8: トップページ判定（旧手順7 - ハイブリッド方式 - サブエージェント版）

住所がマッチし、かつ収集対象と判定されたURLについて、それが施設のトップページか否かを判定します。

#### 第1段階: URL構造による判定

以下のいずれかに該当する場合、トップページと判定：
- ドメイン直下（例: `https://example.com/`, `https://example.com/index.html`）
- パスの深さが浅い（スラッシュが2個以下）

→ トップページと判定された場合は**手順11へ**

#### 第2段階: Claude Codeサブエージェントによる判定

URL構造で判定できない場合、Claude Codeのサブエージェント機能を使って判定します。

##### 処理フロー

1. **ツールが判定依頼レスポンスを出力**:
   ```json
   {
     "action": "request_judgment",
     "facility_name": "東京タワー",
     "url": "https://www.tokyotower.co.jp/about",
     "html_text_preview": "【先頭5000文字のHTMLテキスト】",
     "question": "このページは「東京タワー」の公式サイトのトップページですか？YesまたはNoで答えてください。また、そう判定した理由を列挙してください",
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

{question}

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
   - `--judgment "Yes"` の場合 → **手順11へ**（成功）
   - `--judgment "No"` の場合 → **手順9へ**（ドメインルート探索）

##### HTMLテキストの切り詰め

- **先頭5000文字のみ**を判定に使用
- **根拠**:
  - トップページの重要情報（タイトル、ヘッダー、メインコンテンツ）は通常先頭に配置される
  - 5000文字は約1000トークンに相当（日本語の場合）
  - コンテキスト使用量の最適化

### 手順9: トップページURLの発見（旧手順8）

現在のURLがトップページでない場合、トップページを探索します。

#### 探索方法

1. **ドメインルートに遷移**:
   - `https://example.com/path/to/page` → `https://example.com/`
   - playwright_download_toolでHTMLをダウンロード

2. **再度トップページ判定**:
   - 手順8の判定ロジックを実行（URL構造チェック → 必要に応じてサブエージェント判定）
   - トップページと判定されれば**手順11へ**

3. **HTMLメタタグからの抽出**（オプション）:
   - それでもトップページでない場合
   - HTMLから `<link rel="home">` や `<meta property="og:url">` を抽出
   - 抽出できたURLに対して手順4〜8を再実行

#### 繰り返し回数

- 最大3回までトップページ検索を試行
- **カウント対象**:
  1. 初回のトップページ判定（手順8）
  2. ドメインルートへの遷移後の判定（手順9-1, 9-2）
  3. メタタグから抽出したURLの判定（手順9-3）
- **注意**: 手順9-3で新しいURLに対して手順4〜8を再実行する場合も1回とカウント
- 3回試行してもトップページが見つからなかった場合は**手順10へ**

### 手順10: 結果なしで終了（旧手順9）

以下のいずれかの場合、結果なしで終了：
- トップページが見つからなかった
- 検索結果が0件だった
- すべてのURLで住所がマッチしなかった
- すべてのURLでダウンロードに失敗した
- すべてのURLで公式サイト判定が `not_eligible` だった

```json
{
  "success": false,
  "facility_name": "施設名",
  "input_address": "入力された住所",
  "message": "公式サイトが見つかりませんでした（具体的な理由）"
}
```

### 手順11: 成功レスポンスを返す（旧手順10）

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

  # 初回実行（criteria.txtパス指定）
  python -m officialsite_finder_tool --name "施設名" --address "住所" \
    --criteria-file "/path/to/criteria.txt"

  # 公式サイト判定結果付き実行（v5新規）
  python -m officialsite_finder_tool --name "施設名" --address "住所" \
    --criteria-judgment "eligible|not_eligible" \
    --criteria-pending-url "URL"

  # トップページ判定結果付き実行（v4から継続）
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
- 公式サイト判定依頼レスポンスの処理方法（`request_criteria_judgment`）
- トップページ判定依頼レスポンスの処理方法（`request_judgment`）

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

4. **ツールが公式サイト判定依頼を出力した場合**（v5新規）:
   ```json
   {
     "action": "request_criteria_judgment",
     "facility_name": "東京タワー",
     "url": "https://...",
     "html_text_preview": "...",
     "criteria": "...",
     "question": "..."
   }
   ```

5. **Claude CodeがTask toolでサブエージェントを起動**（公式サイト判定）

6. **サブエージェントが判定結果を返す**（"eligible" または "not_eligible"）

7. **Claude Codeが判定結果でツールを再実行**:
   ```bash
   python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8" \
     --criteria-judgment "eligible" --criteria-pending-url "https://..."
   ```

8. **eligible の場合、ツールがトップページ判定依頼を出力**（v4から継続）:
   ```json
   {
     "action": "request_judgment",
     "facility_name": "東京タワー",
     "url": "https://...",
     "html_text_preview": "...",
     "question": "..."
   }
   ```

9. **Claude CodeがTask toolでサブエージェントを起動**（トップページ判定）

10. **サブエージェントが判定結果を返す**（"Yes" または "No"）

11. **Claude Codeが判定結果でツールを再実行**:
    ```bash
    python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8" \
      --judgment "Yes" --pending-url "https://..."
    ```

12. **ツールが最終結果を出力**（成功または失敗）

13. **Claude Codeがユーザーに結果を報告**

### サブエージェント連携の実装詳細

**ツール側の実装**（公式サイト判定依頼）:

```python
# criteria.txtを読み込む
criteria_file = args.criteria_file or "criteria.txt"
try:
    with open(criteria_file, encoding="utf-8") as f:
        criteria_text = f.read()
except FileNotFoundError:
    logger.warning(f"criteria.txtが見つかりません: {criteria_file} - 手順7をスキップ")
    criteria_text = None

# criteria_textがある場合のみ判定依頼を出力
if criteria_text:
    criteria_judgment_request = {
        "action": "request_criteria_judgment",
        "facility_name": facility_name,
        "url": url,
        "html_text_preview": html_text[:5000],
        "criteria": criteria_text,
        "question": f"このページは criteria.txt の「URL収集対象」に該当しますか？「eligible」（収集対象）または「not_eligible」（収集対象外）で回答し、理由を1行で添えてください。",
        "matched_address": matched_address
    }
    print(json.dumps(criteria_judgment_request, ensure_ascii=False))
    sys.exit(0)  # 判定待ちのため一旦終了
```

**Claude Code側の処理**（SKILL.mdに記載）:

```python
# 1. ツールの出力をパース
output = json.loads(tool_output)

if output.get("action") == "request_criteria_judgment":
    # 2. Task toolでサブエージェントを起動（公式サイト判定）
    result = Task(
        subagent_type="general-purpose",
        description="公式サイト判定",
        prompt=f"""以下のページが「{output['facility_name']}」の公式サイトとして収集対象か判定してください。

URL: {output['url']}

HTMLテキスト:
{output['html_text_preview']}

判定基準:
{output['criteria']}

「eligible」（収集対象）または「not_eligible」（収集対象外）で回答し、理由を1行で添えてください。

Answer: """
    )

    # 3. 判定結果を取得（"eligible" or "not_eligible"）
    criteria_judgment = result.strip()

    # 4. ツールを再実行
    run_tool(
        f"python -m officialsite_finder_tool "
        f"--name '{output['facility_name']}' "
        f"--address '{original_address}' "
        f"--criteria-judgment '{criteria_judgment}' "
        f"--criteria-pending-url '{output['url']}'"
    )

elif output.get("action") == "request_judgment":
    # トップページ判定（v4から継続）
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

    judgment = result.strip()

    run_tool(
        f"python -m officialsite_finder_tool "
        f"--name '{output['facility_name']}' "
        f"--address '{original_address}' "
        f"--judgment '{judgment}' "
        f"--pending-url '{output['url']}'"
    )
```

## エラーハンドリング詳細

### タイムアウト設定

- **HTMLダウンロード**: 30秒（playwright_download_toolのデフォルト）
- **Google検索API**: 30秒（google_search_toolのデフォルト）
- **サブエージェント判定（公式サイト）**: 60秒
- **サブエージェント判定（トップページ）**: 60秒
- **全体処理**: 15分（v5で延長）
  - **根拠**:
    - Google検索: 30秒
    - HTMLダウンロード×5件: 30秒×5 = 150秒
    - 住所抽出・比較: 各10秒×5 = 50秒
    - 公式サイト判定×5回: 60秒×5 = 300秒（v5追加分）
    - トップページ判定×3回: 60秒×3 = 180秒
    - バッファ: 30秒
    - **合計**: 約740秒 ≈ 12.3分（余裕を持たせて15分）

### ログ出力

以下のタイミングでログを出力（推奨）：
- 各手順の開始時・終了時
- エラー発生時（詳細なエラー情報を含む）
- 住所マッチ成功時
- 公式サイト判定依頼時と結果受信時（v5追加）
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
2026-01-03 12:35:01 [INFO] 手順7: 公式サイト判定依頼 - URL: "https://www.tokyotower.co.jp/about"
2026-01-03 12:35:15 [INFO] 手順7: 判定結果受信 - 結果: eligible
2026-01-03 12:35:15 [INFO] 手順8: サブエージェント判定依頼 - URL: "https://www.tokyotower.co.jp/about"
2026-01-03 12:35:25 [INFO] 手順8: 判定結果受信 - 結果: No
2026-01-03 12:35:25 [INFO] 手順9: ドメインルートへ遷移 - URL: "https://www.tokyotower.co.jp/"
2026-01-03 12:35:30 [INFO] 手順8: トップページ判定 - 結果: Yes (URL構造判定)
2026-01-03 12:35:30 [INFO] 手順11: 成功 - 公式サイト発見: "https://www.tokyotower.co.jp/"
```

### リトライポリシー

- **ネットワークエラー**: リトライせず次のURLに進む
- **タイムアウト**: リトライせず次のURLに進む
- **Google Search API エラー**: リトライせず処理を終了
- **一時的なエラー**: 同一URLに対するリトライは行わない（検索結果の次のURLを試行）
- **公式サイト判定エラー**: 不明な回答の場合は次のURLに進む（v5追加）
- **サブエージェント判定エラー**: 不明な回答の場合は次のURLに進む

### 中間結果の保存（オプション）

デバッグやトラブルシューティングのため、以下の中間結果を保存することを推奨：

- **保存内容**:
  - ダウンロードしたHTML（各URL）
  - 抽出した住所（各URL）
  - 公式サイト判定依頼内容と結果（v5追加）
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
  ├── 04_criteria_judgment_request.json   ← v5追加
  ├── 04_criteria_judgment_response.json  ← v5追加
  ├── 05_subagent_request.json
  └── 05_subagent_response.json
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

### criteria.txtの扱い

- criteria.txtが存在しない場合は手順7をスキップして手順8（旧手順7）に進む
- criteria.txtの内容全文をサブエージェントに渡す（切り詰めは行わない）
- `--criteria-file` オプションで任意のパスを指定可能

### サブエージェント判定の最適化

- **HTMLテキストの切り詰め**: 先頭5000文字のみを使用（公式サイト判定・トップページ判定ともに）
  - **根拠**:
    - トップページの重要情報（タイトル、ヘッダー、メインコンテンツ）は通常先頭に配置される
    - 5000文字は約1000トークンに相当（日本語の場合）
- **判定依頼の形式**: シンプルで明確な質問形式
- **回答形式**:
  - 公式サイト判定: eligible/not_eligible の明確な回答 + 理由1行
  - トップページ判定: Yes/No の明確な回答
- **判定基準の明示**: サブエージェントに判定基準を明示的に伝える

### パフォーマンス考慮

- 並列処理は行わず、順次処理を推奨
- 最初にマッチし、かつ収集対象と判定されたURLで処理を終了するため、平均的には1-2件のURL処理で完了
- 最悪ケースでも5件のURL処理で完了
- サブエージェント判定は必要な場合のみ実行（criteria.txtが存在しない場合やURL構造で判定可能な場合はスキップ）

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
- 公式サイト判定: 正しく判定依頼が行われ、結果が処理されるか（v5追加）
- サブエージェント判定: 正しく判定依頼が行われ、結果が処理されるか

### 公式サイト判定テスト（v5追加）

- 収集対象のURLで "eligible" が返されるか
- 収集対象外のURL（ポータルサイト等）で "not_eligible" が返されるか
- 判定結果が正しくツールに渡されるか
- `not_eligible` の場合に次のURLへ進むか
- 5件すべてで `not_eligible` の場合に手順10へ進むか
- criteria.txtが存在しない場合に手順7をスキップするか

### サブエージェント判定テスト（v4から継続）

- トップページのHTMLで "Yes" が返されるか
- サブページのHTMLで "No" が返されるか
- 判定結果が正しくツールに渡されるか
- 判定結果に基づいて適切な処理が行われるか

### エッジケーステスト

- 施設名が一般的すぎる場合（例: 「市役所」）
- 住所が不完全な場合
- HTMLに住所が複数含まれる場合
- トップページでないページがヒットした場合
- ポータルサイトが検索結果に含まれる場合（v5追加）
- criteria.txtが存在しない場合（v5追加）
- サブエージェント判定で不明な回答が返された場合
- ドメインルートもトップページでない場合

## 環境要件

### 必須環境変数

```env
# Google Custom Search API
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
```

### オプションファイル

- **criteria.txt**: 公式サイト判定基準（デフォルト: プロジェクトルート）
  - 存在しない場合は手順7をスキップ

### Pythonパッケージ

- Python 3.8以上
- 各ツールの依存パッケージ（requirements.txtまたはpyproject.toml参照）

## バージョン履歴

### v5.0 (2026-02-27)

**主要変更:**
- **公式サイト判定ステップを追加（手順7）**: criteria.txtの基準に基づき「このURLは収集対象か」をサブエージェントが判定する手順を新規追加
- **手順番号の繰り下げ**: 既存の手順7〜10を手順8〜11に変更
- **新しい判定依頼レスポンス形式を追加**: `action: "request_criteria_judgment"` 形式を導入
- **新しいツール引数を追加**: `--criteria-judgment` と `--criteria-pending-url`
- **`--criteria-file` オプションを追加**: criteria.txtのパスを任意指定可能
- **タイムアウト設定を更新**: 公式サイト判定×5回（60秒×5=300秒）を追加し、全体を15分に変更
- **ログ出力を更新**: 公式サイト判定依頼と結果受信のログを追加
- **デバッグファイル構成を更新**: criteria_judgment_request/responseファイルを追加

**技術的改善:**
- ポータルサイト・予約サイト等の収集対象外URLを自動除外
- criteria.txtの柔軟な読み込み（ファイルが存在しない場合はスキップ）
- 判定根拠をサブエージェントが出力することで透明性向上

**互換性:**
- 出力形式（成功・失敗レスポンス）はv4と互換
- 新たに `request_criteria_judgment` 判定依頼レスポンス形式を追加
- ツールのコマンドライン引数に `--criteria-judgment` と `--criteria-pending-url` を追加
- `--judgment` と `--pending-url` は引き続き有効

### v4.0 (2026-01-03)

**主要変更:**
- **Claude API呼び出しを削除**: Claude Code自身がサブエージェントを起動して判定を行う方式に変更
- **サブエージェント連携の実装**: Task toolを使ったサブエージェント起動フローを追加
- **判定依頼レスポンス形式を追加**: `action: "request_judgment"` 形式を導入
- **環境変数の削減**: `ANTHROPIC_API_KEY` が不要に（`GOOGLE_API_KEY`と`GOOGLE_CSE_ID`のみ）

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

v5では、住所マッチ後に criteria.txt の判定基準を用いて「収集対象か否か」を確認する手順7を追加することで：

1. **精度向上**: ポータルサイト・予約サイト等の収集対象外URLを自動除外
2. **柔軟な基準管理**: criteria.txtを更新するだけで判定基準を変更可能
3. **透明性の確保**: サブエージェントが判定根拠を出力することで、なぜそのURLが選ばれたか確認可能
4. **後方互換性**: v4の既存フロー（トップページ判定）をそのまま維持

この変更により、より実用的で精度の高い公式サイト発見システムを実現しました。
