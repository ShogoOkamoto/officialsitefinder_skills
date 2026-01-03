"""Google Search CLI Tool.

A command-line tool that utilizes Google Custom Search (CSE)
to retrieve information from the internet and return results in JSON format.
"""

import json
import os
import sys
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google Custom Search API configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


def search(query: str, num_results: int = 10) -> Dict[str, Any]:
    """Search the web using Google Custom Search.

    Args:
        query: The search query string.
        num_results: Number of results to return (1-10, default 10).

    Returns:
        Dictionary containing either search results or error information.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return {
            "error": "GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set."
        }

    num_results = max(1, min(10, num_results))

    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(GOOGLE_SEARCH_URL, params=params)

            if response.status_code != 200:
                return {
                    "error": f"Search request failed with status {response.status_code}: {response.text}"
                }

            try:
                data = response.json()
            except ValueError:
                return {"error": "Failed to parse response as JSON"}

        items = data.get("items", [])
        if not items:
            return {"results": [], "count": 0}

        results: List[Dict[str, str]] = []
        for item in items:
            result = {
                "title": item.get("title", "No title"),
                "link": item.get("link", "No link"),
                "snippet": item.get("snippet", "No description"),
            }
            results.append(result)

        return {"results": results, "count": len(results)}

    except httpx.TimeoutException:
        return {"error": "Request timeout"}
    except httpx.RequestError as e:
        return {"error": f"Request error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def main() -> None:
    """CLI entry point."""
    import argparse
    import io

    # Fix Windows console encoding for UTF-8 output
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="Google Custom Search CLI Tool - Search the web and get JSON results"
    )
    parser.add_argument("query", help="Search query string")
    parser.add_argument(
        "-n",
        "--num-results",
        type=int,
        default=10,
        help="Number of results to return (1-10, default: 10)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )

    args = parser.parse_args()

    result = search(args.query, args.num_results)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))

    # Exit with error code if there was an error
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
