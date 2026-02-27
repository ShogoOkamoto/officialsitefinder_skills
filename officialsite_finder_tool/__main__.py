#!/usr/bin/env python3
"""
Official Site Finder Tool v5

Finds the official website top page of a facility by:
1. Extracting address from user input
2. Searching Google
3. Downloading HTML and matching addresses
4. Using Claude Code subagent to determine if URL is eligible per criteria.txt (v5)
5. Using Claude Code subagent to determine if page is top page
"""

import argparse
import json
import subprocess
import sys
import os
from urllib.parse import urlparse
from pathlib import Path
import io

# Force UTF-8 encoding for stdout and stderr (Windows compatibility)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set environment variable for subprocess calls
os.environ['PYTHONIOENCODING'] = 'utf-8'


def extract_address(text):
    """Extract Japanese address (prefecture + city) from text using extract_address_tool."""
    try:
        result = subprocess.run(
            ["python", "-m", "extract_address_tool.extract"],
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
        print(f"[WARNING] Address extraction failed: {e}", file=sys.stderr)
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


def download_html(url, format_type="text"):
    """Download HTML using playwright_download_tool."""
    try:
        tool_dir = Path(__file__).parent.parent / "playwright_download_tool"

        result = subprocess.run(
            ["python", "download.py", url, f"--format={format_type}"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(tool_dir),
            encoding="utf-8"
        )

        if result.returncode != 0:
            return None

        return result.stdout

    except Exception as e:
        print(f"[WARNING] HTML download failed for {url}: {e}", file=sys.stderr)
        return None


def compare_addresses(addr1, addr2):
    """Compare two addresses using compare_address_tool."""
    try:
        result = subprocess.run(
            ["python", "-m", "compare_address_tool.compare_address_tool", addr1, addr2],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8"
        )

        # Exit code 0 means match, 1 means no match
        return result.returncode == 0

    except Exception as e:
        print(f"[WARNING] Address comparison failed: {e}", file=sys.stderr)
        return False


def is_top_page_by_url(url):
    """Check if URL is likely a top page based on URL structure (domain root only)."""
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')

        # Domain root or simple index files only
        if path in ('', '/index.html', '/index.php', '/index.htm'):
            return True

        return False

    except Exception:
        return False


def get_domain_root(url):
    """Get the domain root URL from a full URL."""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        return None


def load_criteria(criteria_file):
    """Load criteria.txt content. Returns None if file not found."""
    try:
        with open(criteria_file, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"[WARNING] Failed to read criteria file {criteria_file}: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Find the official website of a facility by name and address"
    )
    parser.add_argument("--name", required=True, help="Facility name")
    parser.add_argument("--address", required=True, help="Facility address")
    # Top page judgment (v4)
    parser.add_argument("--judgment", help="Top page judgment from Claude Code (Yes/No)")
    parser.add_argument("--pending-url", help="URL pending top page judgment")
    # Criteria judgment (v5)
    parser.add_argument("--criteria-judgment", help="Criteria eligibility judgment (eligible/not_eligible)")
    parser.add_argument("--criteria-pending-url", help="URL pending criteria judgment")
    parser.add_argument("--criteria-file", help="Path to criteria.txt (default: criteria.txt in project root)")
    parser.add_argument("--matched-address", help="Matched address (passed back after judgment)")
    parser.add_argument("--skip-urls", help="JSON array of URLs to skip in search loop")
    # Search result reuse (skip re-searching Google)
    parser.add_argument("--search-results", help="JSON array of previous search results (skips Google search)")
    parser.add_argument("--target-address", help="Pre-extracted target address (skips address extraction)")

    args = parser.parse_args()

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

    # Load criteria.txt (default: criteria.txt in CWD; override with --criteria-file)
    criteria_path = args.criteria_file if args.criteria_file else "criteria.txt"
    criteria_text = load_criteria(criteria_path)
    if criteria_text:
        print(f"[INFO] Loaded criteria.txt from {criteria_path}", file=sys.stderr)
    else:
        print(f"[WARNING] criteria.txt not found at {criteria_path} - step 7 (criteria judgment) will be skipped", file=sys.stderr)

    # Build skip_urls set
    skip_urls = set()
    if args.skip_urls:
        try:
            skip_urls = set(json.loads(args.skip_urls))
        except Exception:
            pass

    # Handle top page judgment result (v4: --judgment + --pending-url)
    if args.judgment and args.pending_url:
        print(f"[INFO] Processing top page judgment: {args.judgment} for URL: {args.pending_url}", file=sys.stderr)
        matched_address = args.matched_address or ""

        if args.judgment.lower() == "yes":
            print(json.dumps({
                "success": True,
                "facility_name": facility_name,
                "input_address": facility_address,
                "official_site_url": args.pending_url,
                "matched_address": matched_address,
                "message": "公式サイトのトップページを発見しました"
            }, ensure_ascii=False))
            sys.exit(0)
        else:
            # Not top page, try domain root
            domain_root = get_domain_root(args.pending_url)
            if domain_root and domain_root != args.pending_url:
                print(f"[INFO] Step 9: Trying domain root: {domain_root}", file=sys.stderr)
                html_text = download_html(domain_root, "text")
                if html_text:
                    if is_top_page_by_url(domain_root):
                        print(json.dumps({
                            "success": True,
                            "facility_name": facility_name,
                            "input_address": facility_address,
                            "official_site_url": domain_root,
                            "matched_address": matched_address,
                            "message": "公式サイトのトップページを発見しました"
                        }, ensure_ascii=False))
                        sys.exit(0)
                    else:
                        print(json.dumps({
                            "action": "request_judgment",
                            "facility_name": facility_name,
                            "url": domain_root,
                            "html_text_preview": html_text[:5000],
                            "question": f"このページは「{facility_name}」の公式サイトのトップページですか？YesまたはNoで答えてください。また、そう判定した理由を列挙してください",
                            "matched_address": matched_address
                        }, ensure_ascii=False))
                        sys.exit(0)

            print(json.dumps({
                "success": False,
                "facility_name": facility_name,
                "input_address": facility_address,
                "message": "トップページが見つかりませんでした"
            }, ensure_ascii=False))
            sys.exit(1)

    # Handle criteria judgment result (v5: --criteria-judgment + --criteria-pending-url)
    if args.criteria_judgment and args.criteria_pending_url:
        print(f"[INFO] Processing criteria judgment: {args.criteria_judgment} for URL: {args.criteria_pending_url}", file=sys.stderr)
        matched_address = args.matched_address or ""

        if args.criteria_judgment.lower() == "eligible":
            url = args.criteria_pending_url
            print(f"[INFO] Step 8: Top page judgment for eligible URL: {url}", file=sys.stderr)

            if is_top_page_by_url(url):
                print(f"[INFO] URL is top page (by structure)", file=sys.stderr)
                print(json.dumps({
                    "success": True,
                    "facility_name": facility_name,
                    "input_address": facility_address,
                    "official_site_url": url,
                    "matched_address": matched_address,
                    "message": "公式サイトのトップページを発見しました"
                }, ensure_ascii=False))
                sys.exit(0)

            # Re-download HTML for top page judgment
            html_text = download_html(url, "text")
            if html_text:
                print(json.dumps({
                    "action": "request_judgment",
                    "facility_name": facility_name,
                    "url": url,
                    "html_text_preview": html_text[:5000],
                    "question": f"このページは「{facility_name}」の公式サイトのトップページですか？YesまたはNoで答えてください。また、そう判定した理由を列挙してください",
                    "matched_address": matched_address
                }, ensure_ascii=False))
                sys.exit(0)
            else:
                # Download failed, skip URL and fall through to search
                print(f"[WARNING] HTML re-download failed for eligible URL: {url}, continuing search", file=sys.stderr)
                skip_urls.add(url)

        elif args.criteria_judgment.lower() == "not_eligible":
            # Add to skip list and fall through to re-run search
            print(f"[INFO] URL not eligible, skipping: {args.criteria_pending_url}", file=sys.stderr)
            skip_urls.add(args.criteria_pending_url)

    # Step 2: Extract address from input (skip if --target-address provided)
    if args.target_address:
        target_address = args.target_address
        print(f"[INFO] Step 2: Using provided target address: {target_address}", file=sys.stderr)
    else:
        print(f"[INFO] Step 2: Extracting address from: {facility_address}", file=sys.stderr)
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
        print(f"[INFO] Extracted address: {target_address}", file=sys.stderr)

    # Step 3: Google search (skip if --search-results provided)
    if args.search_results:
        try:
            provided = json.loads(args.search_results)
            if isinstance(provided, list):
                search_results = {"results": provided, "count": len(provided)}
            else:
                search_results = provided
            print(f"[INFO] Step 3: Using provided search results ({search_results.get('count', 0)} URLs)", file=sys.stderr)
        except Exception as e:
            print(f"[WARNING] Failed to parse --search-results: {e}, falling back to Google search", file=sys.stderr)
            args.search_results = None

    if not args.search_results:
        print(f"[INFO] Step 3: Searching Google for: {facility_name} {target_address}", file=sys.stderr)
        query = f"{facility_name} {target_address}"
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

        print(f"[INFO] Found {len(search_results['results'])} search results", file=sys.stderr)
        for i, r in enumerate(search_results["results"]):
            print(f"[INFO]   [{i+1}] {r['link']}", file=sys.stderr)

    # Steps 4-7: Process each URL
    for idx, result in enumerate(search_results["results"]):
        url = result["link"]

        # Skip PDF files
        if url.lower().endswith('.pdf'):
            print(f"[INFO] Skipping PDF: {url}", file=sys.stderr)
            continue

        # Skip previously processed/rejected URLs
        if url in skip_urls:
            print(f"[INFO] Skipping previously processed URL: {url}", file=sys.stderr)
            continue

        print(f"[INFO] Step 4: Downloading HTML from URL {idx+1}: {url}", file=sys.stderr)

        # Step 4: Download HTML
        html_text = download_html(url, "text")
        if not html_text:
            print(f"[WARNING] Step 4: Failed to download HTML from {url}", file=sys.stderr)
            continue

        # Step 5: Extract addresses from HTML
        page_addresses = extract_address(html_text)
        if not page_addresses:
            print(f"[WARNING] Step 5: No addresses found on {url}", file=sys.stderr)
            continue

        print(f"[INFO] Step 5: Found {len(page_addresses)} addresses on page", file=sys.stderr)

        # Step 6: Compare addresses
        address_matched = False
        matched_address = None

        for page_addr in page_addresses:
            if compare_addresses(target_address, page_addr):
                address_matched = True
                matched_address = page_addr
                print(f"[INFO] Step 6: Address matched: {matched_address}", file=sys.stderr)
                break

        if not address_matched:
            print(f"[WARNING] Step 6: No address match on {url}", file=sys.stderr)
            continue

        # Step 7: Criteria judgment (v5 - using criteria.txt)
        if criteria_text:
            print(f"[INFO] Step 7: Requesting criteria judgment for {url}", file=sys.stderr)
            print(json.dumps({
                "action": "request_criteria_judgment",
                "facility_name": facility_name,
                "url": url,
                "html_text_preview": html_text[:5000],
                "criteria": criteria_text,
                "question": f"このページは criteria.txt の「URL収集対象」に該当しますか？「eligible」（収集対象）または「not_eligible」（収集対象外）で回答し、理由を列挙して添えてください。",
                "matched_address": matched_address,
                "search_results": search_results.get("results", []),
                "target_address": target_address
            }, ensure_ascii=False))
            sys.exit(0)

        # Step 8: Top page judgment
        print(f"[INFO] Step 8: Top page judgment for {url}", file=sys.stderr)

        if is_top_page_by_url(url):
            print(f"[INFO] URL is top page (by structure)", file=sys.stderr)
            print(json.dumps({
                "success": True,
                "facility_name": facility_name,
                "input_address": facility_address,
                "official_site_url": url,
                "matched_address": matched_address,
                "message": "公式サイトのトップページを発見しました"
            }, ensure_ascii=False))
            sys.exit(0)

        print(f"[INFO] Step 8: Requesting top page judgment from Claude Code", file=sys.stderr)
        print(json.dumps({
            "action": "request_judgment",
            "facility_name": facility_name,
            "url": url,
            "html_text_preview": html_text[:5000],
            "question": f"このページは「{facility_name}」の公式サイトのトップページですか？YesまたはNoで答えてください。また、そう判定した理由を列挙してください",
            "matched_address": matched_address
        }, ensure_ascii=False))
        sys.exit(0)

    # No results found
    print(json.dumps({
        "success": False,
        "facility_name": facility_name,
        "input_address": facility_address,
        "message": "住所が一致する公式サイトが見つかりませんでした"
    }, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
