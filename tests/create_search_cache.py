"""Google検索結果キャッシュ生成スクリプト。

sample_from_scuel_10.tsv の全施設に対してGoogle検索を実行し、
結果を tests/resource/search_cache.json に保存する。

テスト実行前に一度だけ実行すればよい。再実行すると全エントリを上書きする。

実行方法:
    python tests/create_search_cache.py

必要な環境変数（.env ファイルまたは環境変数として設定）:
    GOOGLE_API_KEY
    GOOGLE_CSE_ID
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).parent.parent
TSV_PATH = PROJECT_ROOT / "tests" / "resource" / "sample_from_scuel_10.tsv"
CACHE_PATH = PROJECT_ROOT / "tests" / "resource" / "search_cache.json"


def extract_full_address(text: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "extract_full_address_tool.extract"],
        input=text,
        capture_output=True,
        text=True,
        timeout=10,
        encoding="utf-8",
        cwd=str(PROJECT_ROOT),
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        return []
    return json.loads(result.stdout.strip())


def extract_city_address(text: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "extract_address_tool"],
        input=text,
        capture_output=True,
        text=True,
        timeout=10,
        encoding="utf-8",
        cwd=str(PROJECT_ROOT),
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        return []
    return json.loads(result.stdout.strip())


def google_search(query: str, num_results: int = 5) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "google_search_tool", query, "-n", str(num_results)],
        capture_output=True,
        text=True,
        timeout=30,
        encoding="utf-8",
        cwd=str(PROJECT_ROOT),
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        raise RuntimeError(f"google_search_tool failed: {result.stderr}")
    return json.loads(result.stdout.strip())


def load_tsv() -> list[tuple[str, str, str]]:
    rows = []
    with open(TSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            name = row["施設名"].strip()
            address = row["都道府県"].strip() + row["住所"].strip()
            expected_url = row["HP_改行削除"].strip()
            rows.append((name, address, expected_url))
    return rows


def main():
    rows = load_tsv()
    cache = {}

    print(f"対象施設数: {len(rows)}")
    print(f"キャッシュ保存先: {CACHE_PATH}")
    print()

    for i, (name, address, _) in enumerate(rows, 1):
        print(f"[{i}/{len(rows)}] {name}")

        # フル住所を抽出（手順6の住所照合に使用）
        full_addrs = extract_full_address(address)
        if not full_addrs:
            print(f"  [ERROR] フル住所の抽出に失敗しました: {address}")
            sys.exit(1)
        target_address = full_addrs[0]
        print(f"  target_address: {target_address}")

        # 市区町村レベル住所を抽出（検索クエリに使用）
        city_addrs = extract_city_address(address)
        search_address = city_addrs[0] if city_addrs else target_address
        print(f"  search_address: {search_address}")

        # Google検索
        query = f"{name} {search_address}"
        print(f"  query: {query}")
        try:
            results = google_search(query, num_results=5)
        except Exception as e:
            print(f"  [ERROR] Google検索に失敗しました: {e}")
            sys.exit(1)

        search_results = results.get("results", [])
        print(f"  検索結果: {len(search_results)}件")
        for j, r in enumerate(search_results, 1):
            print(f"    [{j}] {r['link']}")

        cache[name] = {
            "target_address": target_address,
            "search_results": search_results,
        }
        print()

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"キャッシュを保存しました: {CACHE_PATH}")


if __name__ == "__main__":
    main()
