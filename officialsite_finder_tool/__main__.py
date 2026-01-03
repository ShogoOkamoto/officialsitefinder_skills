#!/usr/bin/env python3
"""
Official Site Finder Tool

Finds the official website top page of a facility by:
1. Extracting address from user input
2. Searching Google
3. Downloading HTML and matching addresses
4. Using Claude Code subagent to determine if page is top page
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

        # Parse JSON output
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

        # Parse JSON output
        search_results = json.loads(result.stdout.strip())
        return search_results

    except Exception as e:
        return {"error": f"Search error: {e}"}


def download_html(url, format_type="text"):
    """Download HTML using playwright_download_tool."""
    try:
        # Change to playwright_download_tool directory
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
    """Check if URL is likely a top page based on URL structure."""
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')

        # Domain root
        if not path or path == '' or path == '/index.html' or path == '/index.php':
            return True

        # Shallow path (2 or fewer slashes)
        if path.count('/') <= 2:
            return True

        return False

    except:
        return False


def get_domain_root(url):
    """Get the domain root URL from a full URL."""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/"
    except:
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Find the official website of a facility by name and address"
    )
    parser.add_argument("--name", required=True, help="Facility name")
    parser.add_argument("--address", required=True, help="Facility address")
    parser.add_argument("--judgment", help="Top page judgment from Claude Code (Yes/No)")
    parser.add_argument("--pending-url", help="URL pending judgment")

    args = parser.parse_args()

    facility_name = args.name.strip()
    facility_address = args.address.strip()
    judgment = args.judgment
    pending_url = args.pending_url

    # Step 1: Input validation
    if not facility_name or not facility_address:
        print(json.dumps({
            "success": False,
            "facility_name": facility_name,
            "input_address": facility_address,
            "message": "入力エラー: 施設名称と住所は必須です"
        }, ensure_ascii=False))
        sys.exit(1)

    # If we have a judgment, process it
    if judgment and pending_url:
        print(f"[INFO] Processing judgment: {judgment} for URL: {pending_url}", file=sys.stderr)

        if judgment.lower() == "yes":
            # This is the top page
            print(json.dumps({
                "success": True,
                "facility_name": facility_name,
                "input_address": facility_address,
                "official_site_url": pending_url,
                "matched_address": "",  # Would need to store this
                "message": "公式サイトのトップページを発見しました"
            }, ensure_ascii=False))
            sys.exit(0)
        else:
            # Not top page, try domain root
            domain_root = get_domain_root(pending_url)
            if domain_root and domain_root != pending_url:
                print(f"[INFO] Trying domain root: {domain_root}", file=sys.stderr)

                # Download domain root HTML
                html_text = download_html(domain_root, "text")
                if html_text:
                    # Check if it's top page by URL
                    if is_top_page_by_url(domain_root):
                        print(json.dumps({
                            "success": True,
                            "facility_name": facility_name,
                            "input_address": facility_address,
                            "official_site_url": domain_root,
                            "matched_address": "",
                            "message": "公式サイトのトップページを発見しました"
                        }, ensure_ascii=False))
                        sys.exit(0)
                    else:
                        # Request judgment for domain root
                        print(json.dumps({
                            "action": "request_judgment",
                            "facility_name": facility_name,
                            "url": domain_root,
                            "html_text_preview": html_text[:5000],
                            "question": f"このページは「{facility_name}」の公式サイトのトップページですか？YesまたはNoで答えてください。"
                        }, ensure_ascii=False))
                        sys.exit(0)

            # Could not find top page
            print(json.dumps({
                "success": False,
                "facility_name": facility_name,
                "input_address": facility_address,
                "message": "トップページが見つかりませんでした"
            }, ensure_ascii=False))
            sys.exit(1)

    # Step 2: Extract address from input
    print(f"[INFO] Step 2: Extracting address from input", file=sys.stderr)
    extracted_addresses = extract_address(facility_address)

    if not extracted_addresses:
        print(json.dumps({
            "success": False,
            "facility_name": facility_name,
            "input_address": facility_address,
            "message": "住所の抽出に失敗しました"
        }, ensure_ascii=False))
        sys.exit(1)

    # Use the first extracted address (prefecture + city)
    target_address = extracted_addresses[0]
    print(f"[INFO] Extracted address: {target_address}", file=sys.stderr)

    # Step 3: Google search
    print(f"[INFO] Step 3: Searching Google", file=sys.stderr)
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

    # Step 4-6: Process each URL
    for idx, result in enumerate(search_results["results"]):
        url = result["link"]

        # Skip PDF files
        if url.lower().endswith('.pdf'):
            print(f"[INFO] Skipping PDF: {url}", file=sys.stderr)
            continue

        print(f"[INFO] Processing URL {idx+1}: {url}", file=sys.stderr)

        # Step 4: Download HTML
        html_text = download_html(url, "text")
        if not html_text:
            print(f"[WARNING] Failed to download HTML from {url}", file=sys.stderr)
            continue

        # Step 5: Extract addresses from HTML
        page_addresses = extract_address(html_text)
        if not page_addresses:
            print(f"[WARNING] No addresses found on {url}", file=sys.stderr)
            continue

        print(f"[INFO] Found {len(page_addresses)} addresses on page", file=sys.stderr)

        # Step 6: Compare addresses
        address_matched = False
        matched_address = None

        for page_addr in page_addresses:
            if compare_addresses(target_address, page_addr):
                address_matched = True
                matched_address = page_addr
                print(f"[INFO] Address matched: {matched_address}", file=sys.stderr)
                break

        if not address_matched:
            print(f"[WARNING] No address match on {url}", file=sys.stderr)
            continue

        # Step 7: Top page judgment
        print(f"[INFO] Step 7: Top page judgment for {url}", file=sys.stderr)

        # First check URL structure
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

        # Need Claude Code judgment
        print(f"[INFO] Requesting Claude Code judgment", file=sys.stderr)
        print(json.dumps({
            "action": "request_judgment",
            "facility_name": facility_name,
            "url": url,
            "html_text_preview": html_text[:5000],
            "question": f"このページは「{facility_name}」の公式サイトのトップページですか？YesまたはNoで答えてください。",
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
