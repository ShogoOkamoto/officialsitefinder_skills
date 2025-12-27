# 1. ベースイメージにPythonスリム版を使用
FROM python:3.11-slim

# 環境変数の設定
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 2. 依存関係ファイルをコピー
COPY requirements.txt .

# 3. 最小限の依存関係をインストールしてPlaywrightとChromiumをセットアップ
RUN apt-get update && apt-get install -y --no-install-recommends \
    && pip install --no-cache-dir -r requirements.txt \
    # Chromiumとその実行に必要なシステム依存ライブラリのみをインストール
    && playwright install --with-deps chromium \
    # 不要なファイルを削除して軽量化
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /root/.cache/pip

# 4. スクリプトをコピー
COPY download.py .
COPY extract.py .

# 5. 実行（引数にURLを渡せるようにする）
ENTRYPOINT ["python", "download.py"]