"""HTML to plain text extraction module."""

from bs4 import BeautifulSoup
import re


def extract_text(html: str) -> str:
    """
    Extract plain text from HTML content.

    Args:
        html: HTML string to extract text from

    Returns:
        Extracted plain text with cleaned whitespace

    Raises:
        ValueError: If html is None or empty
    """
    if html is None:
        raise ValueError("HTML content cannot be None")

    if not html.strip():
        raise ValueError("HTML content cannot be empty")

    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Remove script and style elements
    for script in soup(['script', 'style', 'noscript']):
        script.decompose()

    # Get text
    text = soup.get_text()

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text


def extract_text_simple(html: str) -> str:
    """
    Extract plain text from HTML using simple regex (faster but less accurate).

    Args:
        html: HTML string to extract text from

    Returns:
        Extracted plain text
    """
    if html is None:
        raise ValueError("HTML content cannot be None")

    if not html.strip():
        raise ValueError("HTML content cannot be empty")

    # Remove script and style tags with content
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


if __name__ == "__main__":
    import sys

    # Read HTML from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            html_content = f.read()
    else:
        html_content = sys.stdin.read()

    # Extract and print text
    try:
        text = extract_text(html_content)
        print(text)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
