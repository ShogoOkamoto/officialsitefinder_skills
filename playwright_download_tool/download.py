"""Download HTML using Playwright and extract plain text."""

import asyncio
import sys
import io
from playwright.async_api import async_playwright
from extract import extract_text

# Force UTF-8 encoding for stdout/stderr (Windows compatibility)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


async def get_html_and_extract_text(url: str, output_format: str = "text") -> str:
    """
    Download HTML from URL using Playwright and extract plain text.

    Args:
        url: URL to download
        output_format: Output format - "text" for plain text, "html" for raw HTML

    Returns:
        Extracted text or raw HTML content

    Raises:
        Exception: If page loading or text extraction fails
    """
    async with async_playwright() as p:
        # ヘッドレスモードで起動
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle")
            content = await page.content()

            if output_format == "html":
                return content
            else:
                # Extract plain text from HTML
                text = extract_text(content)
                return text
        except Exception as e:
            raise Exception(f"Error downloading or processing {url}: {e}")
        finally:
            await browser.close()


async def main():
    """Main entry point for command-line usage."""
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python download.py <URL> [--format=text|html]", file=sys.stderr)
        print("Example: python download.py https://example.com", file=sys.stderr)
        print("Example: python download.py https://example.com --format=html", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    output_format = "text"  # Default to text output

    # Parse optional format argument
    if len(sys.argv) > 2 and sys.argv[2].startswith("--format="):
        output_format = sys.argv[2].split("=")[1]
        if output_format not in ["text", "html"]:
            print(f"Error: Invalid format '{output_format}'. Use 'text' or 'html'.", file=sys.stderr)
            sys.exit(1)

    try:
        result = await get_html_and_extract_text(url, output_format)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())