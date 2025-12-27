# Playwright Download Tool

PlaywrightでWebページのHTMLをダウンロードし、プレーンテキストを抽出するDockerツールです。

## 機能

- PlaywrightのChromiumブラウザを使用してJavaScriptで動的に生成されたコンテンツを含むHTMLを取得
- BeautifulSoupを使用してHTMLからプレーンテキストを抽出
- Dockerコンテナで実行可能（環境構築不要）
- ローカル環境でも実行可能

## プロジェクト構成

```
playwright_download_tool/
├── Dockerfile              # Dockerイメージ定義
├── download.py             # HTMLダウンロード & テキスト抽出メインスクリプト
├── extract.py              # HTMLテキスト抽出モジュール
├── requirements.txt        # Python依存関係
├── test_extract.py         # テキスト抽出機能のテストスイート
└── README.md              # このファイル
```

## 使用方法

### Docker を使用する場合（推奨）

#### 1. Dockerイメージをビルド

```bash
docker build -t playwright-download-tool .
```

#### 2. プレーンテキストを抽出

デフォルトでは、ダウンロードしたHTMLからプレーンテキストを抽出します。

```bash
docker run --rm playwright-download-tool https://example.com
```

出力例:
```
Example Domain
Example Domain
This domain is for use in documentation examples without needing permission. Avoid use in operations.
Learn more
```

#### 3. 生のHTMLを取得

`--format=html` オプションを使用すると、生のHTMLを取得できます。

```bash
docker run --rm playwright-download-tool https://example.com --format=html
```

出力例:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Example Domain</title>
    ...
</head>
<body>
    ...
</body>
</html>
```

#### 4. 出力をファイルに保存

```bash
# テキストをファイルに保存
docker run --rm playwright-download-tool https://example.com > output.txt

# HTMLをファイルに保存
docker run --rm playwright-download-tool https://example.com --format=html > output.html
```

### ローカル環境で使用する場合

#### 1. 依存関係をインストール

```bash
pip install -r requirements.txt
```

#### 2. Playwright Chromiumブラウザをインストール

```bash
python -m playwright install chromium
```

#### 3. スクリプトを実行

```bash
# プレーンテキストを抽出
python download.py https://example.com

# 生のHTMLを取得
python download.py https://example.com --format=html

# ファイルに保存
python download.py https://example.com > output.txt
```

## コマンドラインオプション

```bash
python download.py <URL> [--format=text|html]
```

- `<URL>`: ダウンロードするWebページのURL（必須）
- `--format=text`: プレーンテキストを出力（デフォルト）
- `--format=html`: 生のHTMLを出力

## テキスト抽出モジュールを直接使用

`extract.py`は単独でも使用できます。

### Pythonモジュールとして

```python
from extract import extract_text, extract_text_simple

html = "<html><body><p>Hello World</p></body></html>"

# BeautifulSoupを使用した高精度抽出
text = extract_text(html)
print(text)  # "Hello World"

# 正規表現を使用した軽量抽出
text = extract_text_simple(html)
print(text)  # "Hello World"
```

### コマンドラインから

```bash
# ファイルから読み込み
python extract.py input.html

# 標準入力から読み込み
echo "<p>Hello</p>" | python extract.py

# HTMLファイルのテキストを抽出してファイルに保存
python extract.py input.html > output.txt
```

## テスト

テストスイートを実行するには:

```bash
# すべてのテストを実行
python -m pytest test_extract.py

# 詳細な出力で実行
python -m pytest test_extract.py -v
```

## 技術仕様

### 使用技術

- **Python 3.11**: プログラミング言語
- **Playwright**: ヘッドレスブラウザ自動化
- **BeautifulSoup4**: HTML解析・テキスト抽出
- **lxml**: 高速HTMLパーサー
- **Docker**: コンテナ化

### 依存関係

```
beautifulsoup4>=4.12.0  # HTML解析
lxml>=5.0.0             # 高速パーサー
pytest>=8.0.0           # テストフレームワーク
pytest-asyncio>=0.23.0  # 非同期テスト
playwright>=1.40.0      # ブラウザ自動化
```

### テキスト抽出の特徴

- script、style、noscriptタグを自動除去
- HTMLエンティティを自動デコード（&amp;、&lt;、&gt;など）
- 余分な空白を適切にクリーンアップ
- エラーハンドリング（None、空文字列のチェック）

## トラブルシューティング

### Dockerイメージのビルドに時間がかかる

初回ビルド時は、Chromiumブラウザと依存関係のダウンロードに時間がかかります（5-10分程度）。2回目以降はキャッシュが使用されます。

### ローカル環境でのPlaywrightエラー

Playwrightのブラウザがインストールされていない場合:

```bash
python -m playwright install chromium
```

### メモリエラー

大きなWebページを処理する場合、Dockerコンテナにメモリ制限がある場合はメモリを増やしてください:

```bash
docker run --rm -m 2g playwright-download-tool https://example.com
```

## ライセンス

このプロジェクトは自由に使用できます。

## 貢献

バグ報告や機能要望は、GitHubのIssueでお願いします。
