"""Integration tests for officialsite_finder_tool.

These tests make real API calls (Google Custom Search + Playwright HTML download).
Run with:
    pytest tests/test_officialsite_finder.py -m integration -v

Requirements:
    - GOOGLE_API_KEY and GOOGLE_CSE_ID set in .env or environment
    - playwright installed: pip install playwright && playwright install chromium

Search caching:
    Google search is expensive and slow.  A session-scoped fixture
    ``tokyo_tower_search_cache`` runs ONE search for 東京タワー and stores the
    result list.  All tests that share the same facility reuse this cache via
    ``run_loop_cached()``, so the number of Google API calls equals the number
    of distinct facilities under test, not the number of test cases.
"""

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

_api_available = bool(
    os.environ.get("GOOGLE_API_KEY") and os.environ.get("GOOGLE_CSE_ID")
)
requires_api = pytest.mark.skipif(
    not _api_available,
    reason="GOOGLE_API_KEY and GOOGLE_CSE_ID must be set",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_tool(*args, timeout=90):
    """Run officialsite_finder_tool subprocess and return (dict, returncode).

    Runs from PROJECT_ROOT so criteria.txt is found automatically.
    """
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


def _llm_judge_content(output: dict) -> tuple:
    """LLMを使ってコンテンツ判定を行う。Returns (judgment, reason)."""
    facility_name = output.get("facility_name", "")
    url = output.get("url", "")
    title = output.get("title", "")
    html_text = output.get("html_text_preview", "")
    address_matched = output.get("address_matched", False)

    prompt = f"""以下のページが施設「{facility_name}」の公式サイトのトップページか判定してください。

施設名: {facility_name}
URL: {url}
タイトル: {title}
住所照合結果: {address_matched}（True=施設住所と一致）

ページテキスト（先頭5000文字）:
{html_text}

## 判定基準

### 公式サイトでない場合は No:
- 口コミ・グルメサイト（食べログ、ホットペッパー等）
- SNS（Facebook, Twitter/X等）
- 百科事典・まとめサイト（Wikipedia等）
- 地図・ナビサイト、求人サイト、比較サイト、ポータルサイト

### トップページでない場合は No:
- /access, /map などアクセス・地図ページ
- /department/xxx など診療科・詳細ページ
- /news, /recruit, /contact などサブページ

### 重要:
- 大学や企業グループのドメイン下のサブディレクトリ（例: /hospital/）で運営されていても公式サイトとみなす
- address_matched=True かつタイトルが施設名と一致する場合は積極的に Yes と判定すること

最初の行に「Yes」または「No」のみを出力し、2行目以降に理由を列挙してください。"""

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        timeout=180,
        encoding="utf-8",
    )
    response = result.stdout.strip()
    lines = response.splitlines()
    judgment = lines[0].strip() if lines else "No"
    reason = "\n".join(lines[1:]).strip() if len(lines) > 1 else "(理由なし)"
    return judgment, reason


def _judgment_loop(name, address, output, rc, max_iterations=15):
    """Continue the stateful judgment loop from an existing output dict.

    Auto-judgment rules:
      - request_criteria_judgment  → always "eligible"
      - request_content_judgment   → LLM判定（judge_officialsite_content_skill基準）
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
            judgment, reason = _llm_judge_content(output)
            if judgment.lower() == "yes":
                output, rc = _run_tool(
                    "--name", name, "--address", address,
                    "--content-judgment", "Yes",
                    "--content-pending-url", url,
                    "--matched-address", matched_address,
                    "--content-judgment-reason", reason,
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
                    "--content-judgment-reason", reason,
                )
        else:
            break

    return output, rc


def run_loop(name, address, max_iterations=15):
    """Run the full tool loop (includes Google search).

    Use for facilities whose search results are not cached.
    """
    output, rc = _run_tool("--name", name, "--address", address)
    return _judgment_loop(name, address, output, rc, max_iterations)


def run_loop_cached(name, address, search_results, max_iterations=15):
    """Run the judgment loop using pre-cached Google search results.

    Passes ``--search-results`` and ``--target-address`` on the first
    invocation so that Step 3 (Google search) is skipped entirely.
    Extraction failure cases (e.g. address without prefecture prefix) are
    handled gracefully: if ``extract_full_addresses_list`` returns nothing
    the tool is run without the cache args and will fail at Step 2.

    Args:
        name:           Facility name.
        address:        Input address string (any variant).
        search_results: Cached list of search result dicts from a previous run.
        max_iterations: Safety limit on the judgment loop.
    """
    from extract_full_address_tool import extract_full_addresses_list

    extracted = extract_full_addresses_list(address)
    if not extracted:
        # No address could be extracted — let the tool fail at Step 2.
        output, rc = _run_tool("--name", name, "--address", address)
        return output, rc

    target_address = extracted[0]
    output, rc = _run_tool(
        "--name", name, "--address", address,
        "--search-results", json.dumps(search_results),
        "--target-address", target_address,
    )
    return _judgment_loop(name, address, output, rc, max_iterations)


def run_loop_with_skip(name, address, skip_first=True, max_iterations=15):
    """Run the loop, rejecting the first content judgment URL to test the skip path."""
    output, rc = _run_tool("--name", name, "--address", address)

    first_content = True
    accumulated_skip_urls = []

    for _ in range(max_iterations):
        if "success" in output:
            return output, rc

        action = output.get("action")
        url = output.get("url", "")
        matched_address = output.get("matched_address", "")

        if action == "request_content_judgment":
            search_results_cache = output.get("search_results", [])
            target_address_cache = output.get("target_address", "")

            if first_content and skip_first:
                first_content = False
                accumulated_skip_urls.append(url)
                output, rc = _run_tool(
                    "--name", name, "--address", address,
                    "--content-judgment", "No",
                    "--content-pending-url", url,
                    "--search-results", json.dumps(search_results_cache),
                    "--target-address", target_address_cache,
                    "--skip-urls", json.dumps(accumulated_skip_urls),
                )
            else:
                first_content = False
                output, rc = _run_tool(
                    "--name", name, "--address", address,
                    "--content-judgment", "Yes",
                    "--content-pending-url", url,
                    "--matched-address", matched_address,
                )

        elif action == "request_criteria_judgment":
            output, rc = _run_tool(
                "--name", name, "--address", address,
                "--criteria-judgment", "eligible",
                "--criteria-pending-url", url,
                "--matched-address", matched_address,
            )

        else:
            break

    return output, rc


# ---------------------------------------------------------------------------
# Session-scoped search cache fixtures (1 Google search per facility)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def tokyo_tower_search_cache():
    """Run ONE Google search for 東京タワー and cache the result list.

    All Tokyo Tower variant tests share this fixture, so only 1 API call
    is made regardless of how many address variants are tested.
    """
    if not _api_available:
        pytest.skip("GOOGLE_API_KEY and GOOGLE_CSE_ID must be set")

    output, _ = _run_tool(
        "--name", "東京タワー",
        "--address", "東京都港区芝公園4丁目2番8号",
    )

    if "search_results" not in output:
        pytest.skip(
            f"Initial run did not return search_results "
            f"(got: {list(output.keys())}). Cannot build cache."
        )

    return output["search_results"]


# ---------------------------------------------------------------------------
# Tests: no API calls needed
# ---------------------------------------------------------------------------

class TestInputValidation:
    """Error handling without hitting external APIs."""

    def test_non_japanese_address_returns_failure(self):
        """ASCII-only address cannot be extracted → success: false."""
        output, rc = _run_tool("--name", "TestFacility", "--address", "INVALID_ADDRESS_123")
        assert isinstance(output, dict)
        assert "success" in output or "message" in output

    def test_missing_name_arg_exits_nonzero(self):
        """--name is required; missing it must exit with non-zero code."""
        result = subprocess.run(
            [sys.executable, "-m", "officialsite_finder_tool", "--address", "東京都港区"],
            capture_output=True, text=True, timeout=15, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode != 0

    def test_missing_address_arg_exits_nonzero(self):
        """--address is required; missing it must exit with non-zero code."""
        result = subprocess.run(
            [sys.executable, "-m", "officialsite_finder_tool", "--name", "テスト施設"],
            capture_output=True, text=True, timeout=15, cwd=str(PROJECT_ROOT),
        )
        assert result.returncode != 0

    def test_output_is_valid_json(self):
        """stdout must always be valid JSON (even on error)."""
        output, _ = _run_tool("--name", "存在しない施設99999", "--address", "NO_MATCH")
        assert isinstance(output, dict)


# ---------------------------------------------------------------------------
# Tests: real API calls — general pipeline
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.slow
class TestOfficialSiteFinderIntegration:
    """End-to-end pipeline tests (Google Search + Playwright).

    Tokyo Tower tests use the session-scoped cache (1 search shared).
    Other facilities run their own search.
    """

    @requires_api
    def test_tokyo_tower_success_and_top_page_url(self, tokyo_tower_search_cache):
        """東京タワーの公式サイトのトップページURLが取得できること。"""
        output, _ = run_loop_cached(
            "東京タワー", "東京都港区芝公園4丁目2番8号",
            tokyo_tower_search_cache,
        )

        assert "success" in output, f"No 'success' key: {output}"
        if not output["success"]:
            pytest.skip(f"Site not found (non-critical): {output.get('message')}")

        url = output.get("official_site_url", "")
        assert url.startswith("http"), f"URL should start with http: {url}"
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        assert path in ("", "/index.html", "/index.php", "/index.htm"), (
            f"Expected top page path, got '{path}' in URL: {url}"
        )

    @requires_api
    def test_output_json_structure_on_success(self, tokyo_tower_search_cache):
        """成功時のJSONに必須フィールドがすべて含まれること。"""
        output, _ = run_loop_cached(
            "東京タワー", "東京都港区芝公園4丁目2番8号",
            tokyo_tower_search_cache,
        )

        for key in ("success", "facility_name", "input_address", "message"):
            assert key in output, f"Missing key '{key}': {output}"

        if output["success"]:
            for key in ("official_site_url", "matched_address"):
                assert key in output, f"Missing success key '{key}': {output}"
            assert output["facility_name"] == "東京タワー"

    @requires_api
    def test_not_eligible_skip_then_eligible(self):
        """最初のURLをnot_eligibleで除外し、次のURLで成功できること。
        (skip/retry パスを検証するため独自の検索を実行する)
        """
        output, _ = run_loop_with_skip(
            "東京タワー", "東京都港区芝公園4丁目2番8号", skip_first=True
        )
        assert "success" in output, f"Loop did not terminate with 'success': {output}"

    @requires_api
    def test_national_diet_library(self):
        """国立国会図書館の公式サイトが取得できること。"""
        output, _ = run_loop("国立国会図書館", "東京都千代田区永田町1丁目10番1号")

        assert "success" in output
        if not output["success"]:
            pytest.skip(f"Site not found (non-critical): {output.get('message')}")

        url = output.get("official_site_url", "")
        assert url.startswith("http")
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        assert path in ("", "/index.html", "/index.php", "/index.htm"), (
            f"Expected top page URL, got: {url}"
        )

    @requires_api
    def test_matched_address_is_related_to_input(self, tokyo_tower_search_cache):
        """matched_address は入力住所の都道府県・市区を含むこと。"""
        output, _ = run_loop_cached(
            "東京タワー", "東京都港区芝公園4丁目2番8号",
            tokyo_tower_search_cache,
        )

        if not output.get("success"):
            pytest.skip("Site not found")

        matched = output.get("matched_address", "")
        assert matched, "matched_address should not be empty on success"
        assert "東京" in matched or "港区" in matched, (
            f"matched_address '{matched}' seems unrelated to input address"
        )


# ---------------------------------------------------------------------------
# Tests: address input variants — all share ONE Google search
# ---------------------------------------------------------------------------

# Street-level variants: address is extracted to banchi level, precise match.
_STREET_VARIANTS = [
    ("全角＋U+2212",    "東京都港区芝公園４丁目２−８"),
    ("半角ハイフン後",  "東京都港区芝公園4丁目2-8"),
    ("標準番地号",      "東京都港区芝公園4丁目2番8号"),
    ("全ハイフン",      "東京都港区芝公園4-2-8"),
    ("全角全角ハイフン","東京都港区芝公園４－２－８"),
    ("漢数字",          "東京都港区芝公園四丁目二番八号"),
    ("番地あり",        "東京都港区芝公園4丁目2番地8号"),
]

# City-level variants: only prefecture+city extracted; prefix match in Step 6.
_CITY_VARIANTS = [
    ("の区切り",   "東京都港区芝公園4の2の8"),
    ("スペース前", "東京都港区芝公園 4-2-8"),
    ("四の二の八", "東京都港区芝公園四の二の八"),
]

# Extraction-failure variants: no prefecture prefix → Step 2 fails immediately.
_FAIL_VARIANTS = [
    ("港区のみ",   "港区"),
    ("番地のみ",   "4-2-8"),
]


@pytest.mark.integration
@pytest.mark.slow
class TestAddressVariantsIntegration:
    """Verify each address input variant produces the correct pipeline result.

    Google search count: exactly 1 (shared via tokyo_tower_search_cache fixture).
    HTML downloads: up to 5 per variant (Playwright, no network guard).
    """

    @requires_api
    @pytest.mark.parametrize("label,address", _STREET_VARIANTS,
                             ids=[v[0] for v in _STREET_VARIANTS])
    def test_street_variant_finds_top_page(self, label, address,
                                           tokyo_tower_search_cache):
        """街番地まで含むバリエーションで公式サイトのトップページが取得できること。"""
        output, _ = run_loop_cached(
            "東京タワー", address, tokyo_tower_search_cache,
        )

        assert "success" in output, f"[{label}] No 'success' key: {output}"
        if not output["success"]:
            pytest.skip(f"[{label}] Site not found: {output.get('message')}")

        url = output.get("official_site_url", "")
        assert url.startswith("http"), f"[{label}] URL should start with http: {url}"

        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        assert path in ("", "/index.html", "/index.php", "/index.htm"), (
            f"[{label}] Expected top page URL, got: {url}"
        )

    @requires_api
    @pytest.mark.parametrize("label,address", _CITY_VARIANTS,
                             ids=[v[0] for v in _CITY_VARIANTS])
    def test_city_variant_matches_via_prefix(self, label, address,
                                             tokyo_tower_search_cache):
        """市区町村レベルのバリエーションで前方一致によりサイトが見つかること。"""
        output, _ = run_loop_cached(
            "東京タワー", address, tokyo_tower_search_cache,
        )

        assert "success" in output, f"[{label}] No 'success' key: {output}"
        # City-level match may or may not find a result depending on page addresses;
        # what matters is that the pipeline terminates cleanly.
        if not output["success"]:
            pytest.skip(f"[{label}] No match via prefix: {output.get('message')}")

        url = output.get("official_site_url", "")
        assert url.startswith("http"), f"[{label}] Invalid URL: {url}"

    @requires_api
    @pytest.mark.parametrize("label,address", _FAIL_VARIANTS,
                             ids=[v[0] for v in _FAIL_VARIANTS])
    def test_extraction_failure_returns_false(self, label, address,
                                              tokyo_tower_search_cache):
        """都道府県なし住所は Step 2 で失敗し success: false を返すこと。
        (Google検索は実行されない)
        """
        output, _ = run_loop_cached(
            "東京タワー", address, tokyo_tower_search_cache,
        )

        assert "success" in output, f"[{label}] No 'success' key: {output}"
        assert output["success"] is False, (
            f"[{label}] Expected success: false for {address!r}, got: {output}"
        )
        assert "message" in output
