"""Google Search MCP Server.

A Model Context Protocol (MCP) server that utilizes Google Custom Search (CSE)
to retrieve information from the internet.
"""

import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env file
load_dotenv()

# Initialize the MCP server
mcp = FastMCP("google-search")

# Google Custom Search API configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID", "")
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"


@mcp.tool()
async def search(query: str, num_results: int = 10) -> str:
    """Search the web using Google Custom Search.

    Args:
        query: The search query string.
        num_results: Number of results to return (1-10, default 10).

    Returns:
        Search results as formatted text.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return "Error: GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set."

    num_results = max(1, min(10, num_results))

    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(GOOGLE_SEARCH_URL, params=params)

        if response.status_code != 200:
            return f"Error: Search request failed with status {response.status_code}: {response.text}"

        try:
            data = response.json()
        except ValueError:
            return "Error: Failed to parse response as JSON"

    items = data.get("items", [])
    if not items:
        return "No results found."

    results = []
    for i, item in enumerate(items, 1):
        title = item.get("title", "No title")
        link = item.get("link", "No link")
        snippet = item.get("snippet", "No description")
        results.append(f"{i}. {title}\n   URL: {link}\n   {snippet}")

    return "\n\n".join(results)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
