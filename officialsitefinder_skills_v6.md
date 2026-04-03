te# 施設公式サイト発見スキル 仕様書 v6

## 概要

施設名称と住所を入力として、Google検索と住所照合により施設の公式サイトのトップページを自動発見するスキルです。

## v6の主な変更点

- **入力住所の抽出を2段階に変更（手順2）**:
  - 番地まで含むフル住所（`extract_full_address_tool`）→ 手順6の住所照合に使用
  - 市区町村レベルの住所（`extract_address_tool`）→ 手順3のGoogle検索クエリに使用
- **Google検索クエリの住所を市区町村レベルに変更（手順3）**: 従来は番地まで含むフル住所をクエリに含めていたが、v6では市区町村レベルの住所のみを使用
- **手順5・6は変更なし**: ページ内住所の抽出（`extract_full_address_tool`）および住所照合（`compare_address_full_tool`）はv5実装のまま継続

### 変更の背景

現行実装（v5相当）では、Google検索クエリに番地まで含むフル住所を使用していた。これにより検索クエリが過剰に詳細になり、Google Custom Searchの関連度スコアに悪影響を与える可能性がある。

v6では検索クエリを市区町村レベルに抑えることでGoogle検索の精度を向上させる。住所照合の精度は `compare_address_full_tool`（漢数字・番地表記の正規化＋前方一致）で引き続き確保する。

---

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

---

## 出力形式

### 成功時

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

### 失敗時

```json
{
  "success": false,
  "facility_name": "施設名",
  "input_address": "入力された住所",
  "message": "公式サイトが見つかりませんでした（具体的な理由）"
}
```

### 公式サイト判定依頼時（v5から継続）

```json
{
  "action": "request_criteria_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/about",
  "html_text_preview": "【先頭5000文字のHTMLテキスト】",
  "criteria": "【criteria.txtの全文】",
  "question": "このページは criteria.txt の「URL収集対象」に該当しますか？「eligible」（収集対象）または「not_eligible」（収集対象外）で回答し、理由を列挙して添えてください。",
  "matched_address": "東京都港区芝公園4-2-8"
}
```

### トップページ判定依頼時（v4から継続）

```json
{
  "action": "request_judgment",
  "facility_name": "東京タワー",
  "url": "https://www.tokyotower.co.jp/about",
  "html_text_preview": "【先頭5000文字のHTMLテキスト】",
  "question": "このページは「東京タワー」の公式サイトのトップページですか？YesまたはNoで答えてください。また、そう判断した根拠を記述してください。",
  "matched_address": "東京都港区芝公園4-2-8"
}
```

---

## 処理フロー

### 手順1: 入力データの検証

- 施設名称と住所が両方とも入力されているか確認
- 入力が不正な場合はエラーを返して終了

### 手順2: 住所から2種類のレベルを抽出 ← v6変更点

入力住所から以下の2種類の住所を抽出する。用途が異なるため別々に取得する。

#### 2-A: フル住所の抽出（手順6の照合に使用）

- **使用ツール**: `extract_full_address_tool`
- **処理内容**: 入力された施設住所から番地まで含む住所を抽出
  - 抽出レベル: 都道府県 + 市区町村 + 丁目・番地・号（例: 「東京都港区芝公園4-2-8」）
- **実行方法**: `python -m extract_full_address_tool.extract`
- **エラー処理**: 住所が抽出できなかった場合はエラーを返して終了

#### 2-B: 市区町村レベルの住所の抽出（手順3の検索クエリに使用）

- **使用ツール**: `extract_address_tool`
- **処理内容**: 入力された施設住所から都道府県〜市区町村レベルの住所を抽出
  - 抽出レベル: 都道府県 + 市区町村（例: 「東京都港区」）
  - 丁目・番地・建物名は抽出されない
- **実行方法**: `python -m extract_address_tool`
- **エラー処理**: 住所が抽出できなかった場合はエラーを返して終了

**例:**

| 入力住所 | 2-A（フル住所） | 2-B（市区町村） |
|---|---|---|
| 東京都港区芝公園4-2-8 | 東京都港区芝公園4-2-8 | 東京都港区 |
| 大阪府大阪市北区梅田2丁目4番9号 | 大阪府大阪市北区梅田2丁目4番9号 | 大阪府大阪市北区 |
| 北海道札幌市中央区北1条西2丁目 | 北海道札幌市中央区北1条西2丁目 | 北海道札幌市中央区 |

### 手順3: Google検索で公式サイト候補を取得 ← v6変更点（クエリ住所を市区町村レベルに変更）

- **使用ツール**: `google_search_tool`
- **検索クエリ構成**: `{施設名称} {手順2-Bで抽出した市区町村レベルの住所}`
  - 例: 「東京タワー 東京都港区」（番地は含めない）
  - 番地まで含めるとクエリが過剰に詳細になりGoogle Custom Searchの関連度に悪影響が出るため除外
- **取得件数**: 最大5件
- **実行方法**: `python -m google_search_tool "query" -n 5`
- **フィルタリング**:
  - PDFファイル（`.pdf`で終わるURL）はスキップ
- **エラー処理**:
  - 検索結果が0件の場合: エラーを返して終了
  - API エラー時: エラーメッセージを返して終了

### 手順4: 各URLのHTMLをダウンロード

- **使用ツール**: `playwright_download_tool`
- **処理内容**: 検索結果のURLを上から順にアクセスし、プレーンテキストを取得
- **実行方法**: `python download.py {URL} --format=text`
- **処理順序**: Google検索結果の上位から順に処理（関連度が高い順）
- **エラー処理**:
  - 404エラー、タイムアウト、認証エラーなどが発生した場合はログに記録し、次のURLに進む
  - 5件すべてダウンロード失敗した場合はエラーを返して終了

### 手順5: HTMLテキストから住所を抽出（変更なし）

- **使用ツール**: `extract_full_address_tool`
- **処理内容**: 取得したプレーンテキストから番地まで含む全ての住所を抽出
- **実行方法**: `python -m extract_full_address_tool.extract`
- **エラー処理**:
  - 住所が抽出できなかった場合（空配列 `[]` が返された場合）は住所情報がないページと判断し、次のURLに進む

### 手順6: 住所の照合（変更なし）

- **使用ツール**: `compare_address_full_tool`
- **処理内容**:
  - 手順2-Aで得られたフル住所と、手順5で抽出された各住所を比較
  - マッチした場合、そのURLを候補として次の手順に進む
- **実行方法**: `python -m compare_address_full_tool "{住所1}" "{住所2}"`
- **比較仕様**:
  - 正規化: 全角→半角・漢数字→アラビア数字・丁目/番地/号→ハイフン表記（NFKC + banchi正規化）
  - 比較方法: 正規化後の前方一致または包含マッチ（詳細度が異なる住所への対応）
  - 表記ゆれ: 全角半角・空白・漢数字の違いは自動吸収
- **複数マッチ時の処理**:
  - 最初にマッチしたURLのみを採用
- **エラー処理**:
  - 5件すべてで住所がマッチしなかった場合はエラーを返して終了

### 手順7: 公式サイト判定（criteria.txt使用 - v5から継続）

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
     "matched_address": "東京都港区芝公園4-2-8"
   }
   ```

2. **Claude CodeがTask toolでサブエージェントを起動**（公式サイト判定）

3. **サブエージェントが判定を実行し、"eligible" または "not_eligible" で回答**

4. **Claude Codeがツールを再実行**:
   ```bash
   python -m officialsite_finder_tool \
     --name "東京タワー" \
     --address "東京都港区芝公園4-2-8" \
     --criteria-judgment "eligible|not_eligible" \
     --criteria-pending-url "https://www.tokyotower.co.jp/about"
   ```

5. **ツールが判定結果を処理**:
   - `eligible` の場合 → **手順8へ**（トップページ判定）
   - `not_eligible` の場合 → 次のURLへ（5件すべてで対象外なら**手順10へ**）

#### 判定基準の概要（criteria.txtより）

**URL収集対象:**
- （１）施設単独サイトのトップページ
- （２）法人・グループサイト内の個別施設紹介ページ
- （３）法人・グループサイト内の個別アクセスページ
- （４）自治体サイト内の公営施設ページ
- （５）医師会サイト内の医師会施設ページ

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
- サブエージェント判定で不明確な回答が返された場合: 次のURLに進む

### 手順8: トップページ判定（v5から継続）

住所がマッチし、かつ収集対象と判定されたURLについて、それが施設のトップページか否かを判定します。

#### 第1段階: URL構造による判定

以下のいずれかに該当する場合、トップページと判定：
- ドメイン直下（例: `https://example.com/`, `https://example.com/index.html`）

→ トップページと判定された場合は**手順11へ**

#### 第2段階: Claude Codeサブエージェントによる判定

URL構造で判定できない場合、Claude Codeのサブエージェント機能を使って判定します。

1. **ツールが判定依頼レスポンスを出力**:
   ```json
   {
     "action": "request_judgment",
     "facility_name": "東京タワー",
     "url": "https://www.tokyotower.co.jp/about",
     "html_text_preview": "【先頭5000文字のHTMLテキスト】",
     "question": "このページは「東京タワー」の公式サイトのトップページですか？YesまたはNoで答えてください。また、そう判定した理由を列挙してください",
     "matched_address": "東京都港区芝公園4-2-8"
   }
   ```

2. **Claude CodeがTask toolでサブエージェントを起動**（トップページ判定）

3. **サブエージェントが "Yes" または "No" で回答**

4. **Claude Codeがツールを再実行**:
   ```bash
   python -m officialsite_finder_tool \
     --name "東京タワー" \
     --address "東京都港区芝公園4-2-8" \
     --judgment "Yes|No" \
     --pending-url "https://www.tokyotower.co.jp/about"
   ```

5. **ツールが判定結果を処理**:
   - `Yes` の場合 → **手順11へ**（成功）
   - `No` の場合 → **手順9へ**（ドメインルート探索）

### 手順9: トップページURLの発見（v5から継続）

現在のURLがトップページでない場合、ドメインルートに遷移して再度手順8の判定を実行します。

1. `https://example.com/path/to/page` → `https://example.com/`
2. playwright_download_toolでHTMLをダウンロード
3. 手順8の判定ロジックを再実行（URL構造チェック → 必要に応じてサブエージェント判定）
4. トップページと判定されれば**手順11へ**、そうでなければ**手順10へ**

### 手順10: 結果なしで終了

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

### 手順11: 成功レスポンスを返す

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

---

## 使用ツール一覧

### 1. extract_full_address_tool

- **場所**: `extract_full_address_tool/`
- **機能**: 日本語テキストから番地まで含むフル住所を抽出してJSON形式で返す
- **用途**: 手順2-A（比較用フル住所の抽出）、手順5（ページ内住所の抽出）
- **実行方法**: `python -m extract_full_address_tool.extract`
- **出力形式**: JSON配列（例: `["東京都港区芝公園4-2-8", "大阪府大阪市北区梅田2-4-9"]`）

### 2. extract_address_tool ← v6新規追加（検索クエリ用）

- **場所**: `extract_address_tool/`
- **機能**: 日本語テキストから市区町村レベルの住所を抽出してJSON形式で返す（番地は含まない）
- **用途**: 手順2-B（Google検索クエリ用の市区町村住所の抽出）
- **実行方法**: `python -m extract_address_tool`
- **出力形式**: JSON配列（例: `["東京都港区", "大阪府大阪市北区"]`）

### 3. google_search_tool

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

### 4. playwright_download_tool

- **場所**: `playwright_download_tool/`
- **機能**: PlaywrightでHTMLダウンロード、BeautifulSoupでプレーンテキスト抽出
- **実行方法**: `python download.py <URL> [--format=text|html]`
- **出力形式**: 標準出力にプレーンテキストまたはHTML

### 5. compare_address_full_tool

- **場所**: `compare_address_full_tool/`
- **機能**: 日本語住所を正規化（全角半角・漢数字・番地表記）して前方一致・包含マッチで比較
- **実行方法**: `python -m compare_address_full_tool "{住所1}" "{住所2}"`
- **出力**:
  - 一致する場合は終了コード 0
  - 一致しない場合は終了コード 1

### 6. officialsite_finder_tool（メインツール）

- **場所**: `officialsite_finder_tool/`
- **機能**: 上記ツールを統合し、公式サイトのトップページを発見
- **実行方法**:
  ```bash
  # 初回実行
  python -m officialsite_finder_tool --name "施設名" --address "住所"

  # 公式サイト判定結果付き実行
  python -m officialsite_finder_tool --name "施設名" --address "住所" \
    --criteria-judgment "eligible|not_eligible" \
    --criteria-pending-url "URL"

  # トップページ判定結果付き実行
  python -m officialsite_finder_tool --name "施設名" --address "住所" \
    --judgment "Yes|No" --pending-url "URL"
  ```

---

## Claude Codeスキルとしての実装

### 実行フロー

1. ユーザーがスキルを起動
2. Claude Codeが施設名と住所を尋ねる
3. Claude Codeがツールを実行:
   ```bash
   python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
   ```
4. ツールが `request_criteria_judgment` を出力した場合、Task toolでサブエージェントを起動（公式サイト判定）
5. 判定結果 (`eligible|not_eligible`) を `--criteria-judgment` で渡してツールを再実行
6. ツールが `request_judgment` を出力した場合、Task toolでサブエージェントを起動（トップページ判定）
7. 判定結果 (`Yes|No`) を `--judgment` で渡してツールを再実行
8. ツールが最終結果を出力
9. Claude Codeがユーザーに結果を報告

---

## エラーハンドリング

### タイムアウト設定

- **HTMLダウンロード**: 30秒
- **Google検索API**: 30秒
- **サブエージェント判定（公式サイト）**: 60秒
- **サブエージェント判定（トップページ）**: 60秒
- **全体処理**: 15分

### リトライポリシー

- **ネットワークエラー**: リトライせず次のURLに進む
- **タイムアウト**: リトライせず次のURLに進む
- **Google Search API エラー**: リトライせず処理を終了
- **サブエージェント判定エラー**: 不明な回答の場合は次のURLに進む

---

## 実装に関する注意事項

### 手順2の2段階抽出（v6の核心）

手順2では同じ入力住所に対して2つのツールを実行し、用途別に住所を保持する：

```python
# 2-A: フル住所（手順6の照合用）
full_addresses = extract_full_address_tool(input_address)
target_address_full = full_addresses[0]  # 例: "東京都港区芝公園4-2-8"

# 2-B: 市区町村レベル（手順3の検索クエリ用）
city_addresses = extract_address_tool(input_address)
target_address_city = city_addresses[0]  # 例: "東京都港区"

# 手順3: 市区町村レベルで検索
query = f"{facility_name} {target_address_city}"

# 手順6: フル住所で照合
compare_address_full_tool(target_address_full, page_address)
```

### compare_address_full_toolの正規化仕様

- 全角→半角変換（NFKC normalization）
- 漢数字→アラビア数字変換（一→1、十一→11 等）
- 番地表記の統一（1丁目2番3号 → 1-2-3）
- 空白除去、小文字化
- 比較方法: 正規化後の前方一致または包含マッチ（詳細度が異なる表記への対応）

### Google検索の最適化

- クエリは `{施設名称} {市区町村レベル住所}` のシンプルな形式
- 番地はクエリに含めない（検索ノイズになりやすいため）

### criteria.txtの扱い

- criteria.txtが存在しない場合は手順7をスキップして手順8に進む
- criteria.txtの内容全文をサブエージェントに渡す

---

## テスト計画

### 手順2の2段階抽出テスト（v6新規）

| 入力住所 | 期待: 2-A（フル） | 期待: 2-B（市区町村） |
|---|---|---|
| 東京都港区芝公園4-2-8 | 東京都港区芝公園4-2-8 | 東京都港区 |
| 大阪府大阪市北区梅田2丁目4番9号 | 大阪府大阪市北区梅田2丁目4番9号 | 大阪府大阪市北区 |
| 青森県上北郡六戸町（番地なし） | 青森県上北郡六戸町 | 青森県上北郡六戸町 |

### 手順3の検索クエリテスト（v6新規）

- 「東京都港区芝公園4-2-8」が入力されたとき、クエリが「施設名 東京都港区」になることを確認
- 番地がクエリに含まれないことを確認

### 手順6の住所照合テスト（変更なし）

| 入力フル住所 | ページ内住所 | 期待 |
|---|---|---|
| 東京都港区芝公園4-2-8 | 東京都港区芝公園4丁目2番8号 | 一致 |
| 東京都港区芝公園4-2-8 | 東京都港区 | 一致（包含マッチ） |
| 東京都港区芝公園4-2-8 | 東京都渋谷区 | 不一致 |

---

## 環境要件

### 必須環境変数

```env
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
```

### オプションファイル

- **criteria.txt**: 公式サイト判定基準（デフォルト: プロジェクトルート）

---

## バージョン履歴

### v6.0 (2026-02-28)

**主要変更:**
- **手順2を2段階に変更**: フル住所（`extract_full_address_tool`）を照合用に、市区町村レベル（`extract_address_tool`）を検索クエリ用に別途抽出
- **手順3の検索クエリを市区町村レベルに変更**: 番地まで含むフル住所をクエリに含めなくなり、Google検索精度を向上
- **手順5・6は変更なし**: `extract_full_address_tool`（ページ内フル住所抽出）と `compare_address_full_tool`（正規化＋前方一致照合）を継続使用

**互換性:**
- 出力形式（成功・失敗・判定依頼レスポンス）はv5と互換
- コマンドライン引数はv5と互換

### v5.0 (2026-02-27)

- 公式サイト判定ステップを追加（手順7）: criteria.txtの基準に基づく収集対象判定
- 新しい判定依頼レスポンス形式: `action: "request_criteria_judgment"`

### v4.0 (2026-01-03)

- Claude APIの直接呼び出しを廃止、Claude Codeのサブエージェント機能を活用
- 判定依頼レスポンス形式を追加: `action: "request_judgment"`

### v3.0〜v1.0

- 詳細はv4.md・v5.md参照

---

## まとめ

v6では手順2に「フル住所抽出（照合用）」と「市区町村抽出（検索用）」の2段階を設けることで：

1. **Google検索精度の向上**: 市区町村レベルのシンプルなクエリでGoogle Custom Searchの関連度を最大化
2. **住所照合精度の維持**: フル住所（番地まで）＋ `compare_address_full_tool` の正規化・前方一致照合により、表記ゆれに強い照合を継続
3. **v5の拡張機能を維持**: criteria.txt判定・トップページ判定はそのまま継続
