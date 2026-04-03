"""Batch integration test: verify official site finder against sample_from_scuel_10.tsv.

Reads tests/resource/sample_from_scuel_10.tsv and for each row:
  1. Runs officialsite_finder_tool with --name and --address (都道府県+住所)
  2. Drives the judgment loop automatically (same rules as test_officialsite_finder.py)
  3. Asserts the found URL matches the expected HP_改行削除 column

検索結果キャッシュについて:
  tests/resource/search_cache.json が存在する場合はキャッシュを使用し、
  Google検索APIを呼び出さない。キャッシュがない施設はスキップされる。

  キャッシュ生成:
      python tests/create_search_cache.py

Run with:
    pytest tests/test_officialsite_finder_batch.py -m integration -v
"""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import pytest

# Load .env (GOOGLE_API_KEY, GOOGLE_CSE_ID)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).parent.parent
TSV_PATH = PROJECT_ROOT / "tests" / "resource" / "sample_from_scuel_10.tsv"
CACHE_PATH = PROJECT_ROOT / "tests" / "resource" / "search_cache.json"

_api_available = bool(
    os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_CSE_ID")
)
requires_api = pytest.mark.skipif(
    not _api_available,
    reason="GOOGLE_API_KEY and GOOGLE_CSE_ID must be set",
)


# ---------------------------------------------------------------------------
# Helpers (same pattern as tests/test_officialsite_finder.py)
# ---------------------------------------------------------------------------

def _run_tool(*args, timeout=90):
    """Run officialsite_finder_tool subprocess and return (dict, returncode)."""
    result = subprocess.run(
        [sys.executable, "-m", "officialsite_finder_tool"] + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        cwd=str(PROJECT_ROOT),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return json.loads(result.stdout.strip()), result.returncode


def _is_top_page_url(url):
    """URL structure heuristic: True if URL is a domain root or simple index page."""
    path = urlparse(url).path.rstrip('/')
    return path in ('', '/index.html', '/index.php', '/index.htm')


def _judgment_loop(name, address, output, rc, max_iterations=15):
    """Continue the stateful judgment loop from an existing output dict.

    Auto-judgment rules:
      - request_criteria_judgment  → always "eligible"
      - request_content_judgment   → "Yes" if URL is a root-level page, "No" otherwise
    """
    accumulated_skip_urls = []

    for _ in range(max_iterations):
        if "success" in output:
            return output, rc

        action = output.get("action")
        url = output.get("url", "")
        matched_address = output.get("matched_address", "")

        if action == "request_criteria_judgment":
            output, rc = _run_tool(
                "--name", name, "--address", address,
                "--criteria-judgment", "eligible",
                "--criteria-pending-url", url,
                "--matched-address", matched_address,
            )
        elif action == "request_content_judgment":
            search_results = output.get("search_results", [])
            target_address = output.get("target_address", "")
            if _is_top_page_url(url):
                output, rc = _run_tool(
                    "--name", name, "--address", address,
                    "--content-judgment", "Yes",
                    "--content-pending-url", url,
                    "--matched-address", matched_address,
                )
            else:
                accumulated_skip_urls.append(url)
                output, rc = _run_tool(
                    "--name", name, "--address", address,
                    "--content-judgment", "No",
                    "--content-pending-url", url,
                    "--search-results", json.dumps(search_results),
                    "--target-address", target_address,
                    "--skip-urls", json.dumps(accumulated_skip_urls),
                )
        else:
            break

    return output, rc


def run_loop_cached(name, address, search_results, target_address, max_iterations=15):
    """キャッシュ済み検索結果を使ってツールを実行（Google検索をスキップ）。"""
    output, rc = _run_tool(
        "--name", name, "--address", address,
        "--search-results", json.dumps(search_results),
        "--target-address", target_address,
    )
    return _judgment_loop(name, address, output, rc, max_iterations)


def _normalize_url(url: str) -> str:
    """Normalize URL for comparison: strip trailing slash, treat http/https as equal."""
    normalized = url.strip().rstrip("/")
    if normalized.startswith("http://"):
        normalized = "https://" + normalized[len("http://"):]
    return normalized


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load_sample_data():
    """Load rows from TSV. Returns list of (name, address, expected_url)."""
    rows = []
    with open(TSV_PATH, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            name = row["施設名"].strip()
            address = row["都道府県"].strip() + row["住所"].strip()
            expected_url = row["HP_改行削除"].strip()
            rows.append((name, address, expected_url))
    return rows


def _load_search_cache() -> dict:
    """tests/resource/search_cache.json を読み込む。存在しない場合は空dictを返す。"""
    if not CACHE_PATH.exists():
        return {}
    with open(CACHE_PATH, encoding="utf-8") as f:
        return json.load(f)


_SAMPLE_DATA = _load_sample_data()


# ---------------------------------------------------------------------------
# Batch test
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.parametrize(
    "name,address,expected_url",
    _SAMPLE_DATA,
    ids=[row[0] for row in _SAMPLE_DATA],
)
@requires_api
def test_officialsite_finder_batch(name, address, expected_url):
    """施設名と住所から公式サイトを検索し、期待URLと一致することを確認する。

    search_cache.json が存在する場合はキャッシュを使用してGoogle検索をスキップする。
    キャッシュがない施設は pytest.skip でスキップされる。
    キャッシュ生成: python tests/create_search_cache.py
    """
    cache = _load_search_cache()
    entry = cache.get(name)

    if entry:
        output, _ = run_loop_cached(
            name, address,
            entry["search_results"],
            entry["target_address"],
        )
    else:
        pytest.skip(
            f"[{name}] search_cache.json にエントリがありません。"
            "python tests/create_search_cache.py を実行してキャッシュを生成してください。"
        )

    assert "success" in output, f"[{name}] No 'success' key in output: {output}"

    if not output["success"]:
        pytest.fail(
            f"[{name}] 公式サイトが見つかりませんでした: {output.get('message')}\n"
            f"  expected: {expected_url}"
        )

    found_url = output.get("official_site_url", "")
    assert _normalize_url(found_url) == _normalize_url(expected_url), (
        f"[{name}] URL mismatch\n"
        f"  found:    {found_url}\n"
        f"  expected: {expected_url}"
    )
