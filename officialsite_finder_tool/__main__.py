#!/usr/bin/env python3
"""
Official Site Finder Tool v6

Finds the official website top page of a facility by:
1. Extracting address from user input
2. Searching Google
3. Downloading HTML
4. Extracting addresses from HTML
5. Comparing addresses (recorded but not used as a skip filter)
6. Requesting judge_officialsite_content_skill judgment for every URL (regardless of address match)
7. Using criteria.txt eligibility judgment (optional, v5+)
"""

import argparse
import json
import subprocess
import sys
import os
from pathlib import Path
import io
import datetime

# Force UTF-8 encoding for stdout and stderr (Windows compatibility)
# Guard prevents double-wrapping in test contexts.
if sys.platform == 'win32':
    if sys.stdout is sys.__stdout__ and hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if sys.stderr is sys.__stderr__ and hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set environment variable for subprocess calls
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Log file path (set in main() after arg parsing)
_log_file = None


def log_print(msg: str):
    """Print to stderr and append to log file (if configured)."""
    print(msg, file=sys.stderr)
    if _log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(_log_file, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} {msg}\n")
        except OSError:
            pass  # don't let logging errors crash the tool


def extract_address(text):
    """Extract Japanese address from text using extract_full_address_tool."""
    try:
        result = subprocess.run(
            ["python", "-m", "extract_full_address_tool.extract"],
            input=text,
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8"
        )

        if result.returncode != 0:
            return []

        addresses = json.loads(result.stdout.strip())
        return addresses if isinstance(addresses, list) else []

    except Exception as e:
        log_print(f"[WARNING] Address extraction failed: {e}")
        return []


def extract_city_address(text):
    """Extract Japanese address up to city/ward level using extract_address_tool."""
    try:
        result = subprocess.run(
            ["python", "-m", "extract_address_tool"],
            input=text,
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8"
        )

        if result.returncode != 0:
            return []

        addresses = json.loads(result.stdout.strip())
        return addresses if isinstance(addresses, list) else []

    except Exception as e:
        log_print(f"[WARNING] City address extraction failed: {e}")
        return []


def google_search(query, num_results=5):
    """Search Google using google_search_tool."""
    try:
        result = subprocess.run(
            ["python", "-m", "google_search_tool", query, "-n", str(num_results)],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8"
        )

        if result.returncode != 0:
            return {"error": f"Search failed: {result.stderr}"}

        search_results = json.loads(result.stdout.strip())
        return search_results

    except Exception as e:
        return {"error": f"Search error: {e}"}


def download_html(url):
    """Download HTML using playwright_download_tool, returning {"title": ..., "text": ...} or None."""
    try:
        tool_dir = Path(__file__).parent.parent / "playwright_download_tool"

        result = subprocess.run(
            ["python", "download.py", url, "--format=json"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(tool_dir),
            encoding="utf-8"
        )

        if result.returncode != 0:
            return None

        return json.loads(result.stdout.strip())

    except Exception as e:
        log_print(f"[WARNING] HTML download failed for {url}: {e}")
        return None


def compare_addresses(addr1, addr2):
    """Compare two addresses using compare_address_full (prefix/containment matching).

    Uses compare_address_full_skill which handles:
    - Full-width/half-width normalization
    - Kanji numeral conversion
    - Banchi notation differences (1丁目2番3号 ↔ 1-2-3)
    - Prefix/containment matching (city-level matches full street address)
    """
    try:
        compare_script = Path(__file__).parent.parent / ".claude" / "skills" / \
            "compare_address_full_skill" / "compare_address_full.py"
        result = subprocess.run(
            ["python", str(compare_script), addr1, addr2],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8"
        )

        # Exit code 0 means match, 1 means no match
        return result.returncode == 0

    except Exception as e:
        log_print(f"[WARNING] Address comparison failed: {e}")
        return False


def load_criteria(criteria_file):
    """Load criteria.txt content. Returns None if file not found."""
    try:
        with open(criteria_file, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        log_print(f"[WARNING] Failed to read criteria file {criteria_file}: {e}")
        return None


def main():
    global _log_file

    parser = argparse.ArgumentParser(
        description="Find the official website of a facility by name and address"
    )
    parser.add_argument("--name", required=True, help="Facility name")
    parser.add_argument("--address", required=True, help="Facility address")
    # Content judgment (v6): judge_officialsite_content_skill result
    parser.add_argument("--content-judgment", help="Content judgment result (Yes/No)")
    parser.add_argument("--content-pending-url", help="URL pending content judgment")
    # Criteria judgment (v5)
    parser.add_argument("--criteria-judgment", help="Criteria eligibility judgment (eligible/not_eligible)")
    parser.add_argument("--criteria-pending-url", help="URL pending criteria judgment")
    parser.add_argument("--criteria-file", help="Path to criteria.txt (default: criteria.txt in project root)")
    parser.add_argument("--matched-address", help="Matched address (passed back after judgment)")
    parser.add_argument("--skip-urls", help="JSON array of URLs to skip in search loop")
    # Search result reuse (skip re-searching Google)
    parser.add_argument("--search-results", help="JSON array of previous search results (skips Google search)")
    parser.add_argument("--target-address", help="Pre-extracted target address (skips address extraction)")
    # Logging
    parser.add_argument("--log-file", default=None, help="Log file path (default: logs/officialsite_finder.log in project root)")
    parser.add_argument("--no-log-file", action="store_true", help="Disable file logging")

    args = parser.parse_args()

    # Initialize log file
    if not args.no_log_file:
        log_path = args.log_file or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs", "officialsite_finder.log"
        )
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        _log_file = log_path

    facility_name = args.name.strip()
    facility_address = args.address.strip()

    # Step 1: Input validation
    if not facility_name or not facility_address:
        print(json.dumps({
            "success": False,
            "facility_name": facility_name,
            "input_address": facility_address,
            "message": "入力エラー: 施設名称と住所は必須です"
        }, ensure_ascii=False))
        sys.exit(1)

    log_print(f"[INFO] ===== 開始: {facility_name} / {facility_address} =====")

    # Load criteria.txt (default: criteria.txt in CWD; override with --criteria-file)
    criteria_path = args.criteria_file if args.criteria_file else "criteria.txt"
    criteria_text = load_criteria(criteria_path)
    if criteria_text:
        log_print(f"[INFO] Loaded criteria.txt from {criteria_path}")
    else:
        log_print(f"[WARNING] criteria.txt not found at {criteria_path} - criteria judgment will be skipped")

    # Build skip_urls set
    skip_urls = set()
    if args.skip_urls:
        try:
            skip_urls = set(json.loads(args.skip_urls))
        except Exception:
            pass

    # Handle content judgment result (v6: --content-judgment + --content-pending-url)
    if args.content_judgment and args.content_pending_url:
        log_print(f"[INFO] === コンテンツ判定結果を受信: {args.content_judgment}")
        log_print(f"[INFO]   URL: {args.content_pending_url}")
        matched_address = args.matched_address or ""

        if args.content_judgment.lower() == "yes":
            log_print(f"[INFO]   → Yes: 公式サイトのトップページと判定")
            url = args.content_pending_url

            if criteria_text:
                log_print(f"[INFO] criteria判定依頼へ進む")
                page_result = download_html(url)
                html_text = page_result["text"] if page_result else ""
                print(json.dumps({
                    "action": "request_criteria_judgment",
                    "facility_name": facility_name,
                    "url": url,
                    "html_text_preview": html_text[:5000],
                    "criteria": criteria_text,
                    "question": f"このページは criteria.txt の「URL収集対象」に該当しますか？「eligible」（収集対象）または「not_eligible」（収集対象外）で回答し、理由を列挙して添えてください。",
                    "matched_address": matched_address,
                    "search_results": [],
                    "target_address": args.target_address or ""
                }, ensure_ascii=False))
                sys.exit(0)
            else:
                log_print(f"[INFO] criteria.txtなし → 直接成功")
                result = {
                    "success": True,
                    "facility_name": facility_name,
                    "input_address": facility_address,
                    "official_site_url": url,
                    "matched_address": matched_address,
                    "message": "公式サイトのトップページを発見しました"
                }
                log_print(f"[INFO] === 結果: 成功 — {url} (matched: {matched_address})")
                print(json.dumps(result, ensure_ascii=False))
                sys.exit(0)

        else:  # No
            log_print(f"[INFO]   → No: 公式サイトのトップページでない → スキップ")
            skip_urls.add(args.content_pending_url)
            # Fall through to URL loop with updated skip_urls

    # Handle criteria judgment result (v5: --criteria-judgment + --criteria-pending-url)
    if args.criteria_judgment and args.criteria_pending_url:
        log_print(f"[INFO] === criteria判定結果を受信: {args.criteria_judgment}")
        log_print(f"[INFO]   URL: {args.criteria_pending_url}")
        matched_address = args.matched_address or ""

        if args.criteria_judgment.lower() == "eligible":
            log_print(f"[INFO]   → eligible: 収集対象と判定 → 成功終了")
            result = {
                "success": True,
                "facility_name": facility_name,
                "input_address": facility_address,
                "official_site_url": args.criteria_pending_url,
                "matched_address": matched_address,
                "message": "公式サイトのトップページを発見しました"
            }
            log_print(f"[INFO] === 結果: 成功 — {args.criteria_pending_url} (matched: {matched_address})")
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(0)

        elif args.criteria_judgment.lower() == "not_eligible":
            log_print(f"[INFO]   → not_eligible: 収集対象外と判定 → スキップして検索結果の次のURLへ")
            skip_urls.add(args.criteria_pending_url)
            # Fall through to URL loop with updated skip_urls

    # Step 2: Extract address from input (skip if --target-address provided)
    if args.target_address:
        target_address = args.target_address
        log_print(f"[INFO] Step 2: Using provided target address: {target_address}")
    else:
        log_print(f"[INFO] Step 2: Extracting address from: {facility_address}")
        extracted_addresses = extract_address(facility_address)

        if not extracted_addresses:
            print(json.dumps({
                "success": False,
                "facility_name": facility_name,
                "input_address": facility_address,
                "message": "住所の抽出に失敗しました"
            }, ensure_ascii=False))
            sys.exit(1)

        target_address = extracted_addresses[0]
        log_print(f"[INFO] Extracted address: {target_address}")

    # Step 3: Google search (skip if --search-results provided)
    if args.search_results:
        try:
            provided = json.loads(args.search_results)
            if isinstance(provided, list):
                search_results = {"results": provided, "count": len(provided)}
            else:
                search_results = provided
            log_print(f"[INFO] Step 3: Using provided search results ({search_results.get('count', 0)} URLs)")
        except Exception as e:
            log_print(f"[WARNING] Failed to parse --search-results: {e}, falling back to Google search")
            args.search_results = None

    if not args.search_results:
        city_addresses = extract_city_address(facility_address)
        search_address = city_addresses[0] if city_addresses else target_address
        log_print(f"[INFO] Step 3: Searching Google for: {facility_name} {search_address}")
        query = f"{facility_name} {search_address}"
        search_results = google_search(query, num_results=5)

        if "error" in search_results:
            print(json.dumps({
                "success": False,
                "facility_name": facility_name,
                "input_address": facility_address,
                "message": f"Google検索エラー: {search_results['error']}"
            }, ensure_ascii=False))
            sys.exit(1)

        if not search_results.get("results") or search_results.get("count", 0) == 0:
            print(json.dumps({
                "success": False,
                "facility_name": facility_name,
                "input_address": facility_address,
                "message": "検索結果が見つかりませんでした"
            }, ensure_ascii=False))
            sys.exit(1)

        log_print(f"[INFO] Step 3: 検索結果 {len(search_results['results'])}件")
        for i, r in enumerate(search_results["results"]):
            log_print(f"[INFO]   [{i+1}] {r['link']}")
            log_print(f"[INFO]       title  : {r.get('title', '(なし)')}")
            snippet = r.get('snippet', '(なし)').replace('\n', ' ')
            log_print(f"[INFO]       snippet: {snippet[:120]}")

    # Steps 4-6: Process each URL
    for idx, result in enumerate(search_results["results"]):
        url = result["link"]

        # Skip PDF files
        if url.lower().endswith('.pdf'):
            log_print(f"[INFO] Skipping PDF: {url}")
            continue

        # Skip previously processed/rejected URLs
        if url in skip_urls:
            log_print(f"[INFO] Skipping previously processed URL: {url}")
            continue

        log_print(f"[INFO] Step 4: HTMLダウンロード開始 [{idx+1}]: {url}")

        # Step 4: Download HTML (returns {"title": ..., "text": ...})
        page_result = download_html(url)
        if not page_result:
            log_print(f"[WARNING] Step 4: HTML取得失敗 → スキップ — {url}")
            continue

        html_text = page_result["text"]
        page_title = page_result["title"]
        log_print(f"[INFO] Step 4: HTML取得成功 ({len(html_text)} 文字) title=\"{page_title}\" — {url}")

        # Step 5: Extract addresses from HTML
        page_addresses = extract_address(html_text)

        # Step 6a: Compare addresses (record result, do NOT skip on mismatch)
        address_matched = False
        matched_address = None

        if page_addresses:
            log_print(f"[INFO] Step 5: ページ内住所 {len(page_addresses)}件")
            for i, addr in enumerate(page_addresses):
                log_print(f"[INFO]   [{i+1}] {addr}")

            log_print(f"[INFO] Step 6a: 住所照合 (target: {target_address})")
            for i, page_addr in enumerate(page_addresses):
                if compare_addresses(target_address, page_addr):
                    address_matched = True
                    matched_address = page_addr
                    log_print(f"[INFO]   比較[{i+1}]: \"{page_addr}\" → 一致")
                    break
                else:
                    log_print(f"[INFO]   比較[{i+1}]: \"{page_addr}\" → 不一致")

            if not address_matched:
                log_print(f"[INFO] Step 6a: 全住所が不一致 (住所照合失敗) — コンテンツ判定は継続")
        else:
            log_print(f"[INFO] Step 5: ページ内住所なし — コンテンツ判定は継続")

        # Step 6b: Request content judgment via judge_officialsite_content_skill
        # (independent of address match result)
        log_print(f"[INFO] Step 6b: コンテンツ判定依頼 (address_matched={address_matched})")
        log_print(f"[INFO]   URL    : {url}")
        log_print(f"[INFO]   title  : {page_title}")
        preview_for_log = html_text[:200].replace('\n', ' ')
        log_print(f"[INFO]   preview: {preview_for_log}")
        print(json.dumps({
            "action": "request_content_judgment",
            "facility_name": facility_name,
            "url": url,
            "title": page_title,
            "html_text_preview": html_text[:5000],
            "address_matched": address_matched,
            "matched_address": matched_address or "",
            "search_results": search_results.get("results", []),
            "target_address": target_address
        }, ensure_ascii=False))
        sys.exit(0)

    # No results found
    log_print(f"[INFO] === 結果: 失敗 — 全検索結果を処理したが公式サイトが見つかりませんでした")
    print(json.dumps({
        "success": False,
        "facility_name": facility_name,
        "input_address": facility_address,
        "message": "公式サイトが見つかりませんでした"
    }, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
