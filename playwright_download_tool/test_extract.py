"""Tests for HTML text extraction module."""

import pytest
from extract import extract_text, extract_text_simple


class TestExtractText:
    """Test suite for extract_text function."""

    def test_simple_html(self):
        """Test extraction from simple HTML."""
        html = "<html><body><p>Hello World</p></body></html>"
        result = extract_text(html)
        assert "Hello World" in result

    def test_nested_tags(self):
        """Test extraction with nested HTML tags."""
        html = """
        <html>
            <body>
                <div>
                    <h1>Title</h1>
                    <p>This is a <strong>test</strong> paragraph.</p>
                </div>
            </body>
        </html>
        """
        result = extract_text(html)
        assert "Title" in result
        assert "This is a test paragraph." in result

    def test_remove_script_tags(self):
        """Test that script tags are removed."""
        html = """
        <html>
            <head>
                <script>console.log('test');</script>
            </head>
            <body>
                <p>Content</p>
                <script>alert('hello');</script>
            </body>
        </html>
        """
        result = extract_text(html)
        assert "Content" in result
        assert "console.log" not in result
        assert "alert" not in result

    def test_remove_style_tags(self):
        """Test that style tags are removed."""
        html = """
        <html>
            <head>
                <style>body { color: red; }</style>
            </head>
            <body>
                <p>Content</p>
            </body>
        </html>
        """
        result = extract_text(html)
        assert "Content" in result
        assert "color: red" not in result

    def test_whitespace_cleanup(self):
        """Test that excessive whitespace is cleaned up."""
        html = """
        <html>
            <body>
                <p>Line 1</p>


                <p>Line 2</p>
            </body>
        </html>
        """
        result = extract_text(html)
        # Should not have excessive blank lines
        assert result.count('\n\n\n') == 0
        assert "Line 1" in result
        assert "Line 2" in result

    def test_empty_html(self):
        """Test that empty HTML raises ValueError."""
        with pytest.raises(ValueError, match="HTML content cannot be empty"):
            extract_text("")

        with pytest.raises(ValueError, match="HTML content cannot be empty"):
            extract_text("   ")

    def test_none_html(self):
        """Test that None HTML raises ValueError."""
        with pytest.raises(ValueError, match="HTML content cannot be None"):
            extract_text(None)

    def test_html_entities(self):
        """Test extraction with HTML entities."""
        html = "<p>AT&amp;T &lt;Company&gt; &quot;test&quot;</p>"
        result = extract_text(html)
        assert "AT&T" in result
        assert "<Company>" in result
        assert '"test"' in result

    def test_multiple_paragraphs(self):
        """Test extraction with multiple paragraphs."""
        html = """
        <html>
            <body>
                <p>First paragraph</p>
                <p>Second paragraph</p>
                <p>Third paragraph</p>
            </body>
        </html>
        """
        result = extract_text(html)
        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert "Third paragraph" in result

    def test_lists(self):
        """Test extraction from lists."""
        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
        """
        result = extract_text(html)
        assert "Item 1" in result
        assert "Item 2" in result
        assert "Item 3" in result

    def test_tables(self):
        """Test extraction from tables."""
        html = """
        <table>
            <tr>
                <td>Cell 1</td>
                <td>Cell 2</td>
            </tr>
            <tr>
                <td>Cell 3</td>
                <td>Cell 4</td>
            </tr>
        </table>
        """
        result = extract_text(html)
        assert "Cell 1" in result
        assert "Cell 2" in result
        assert "Cell 3" in result
        assert "Cell 4" in result

    def test_noscript_tags(self):
        """Test that noscript tags are removed."""
        html = """
        <html>
            <body>
                <p>Content</p>
                <noscript>Please enable JavaScript</noscript>
            </body>
        </html>
        """
        result = extract_text(html)
        assert "Content" in result
        assert "Please enable JavaScript" not in result


class TestExtractTextSimple:
    """Test suite for extract_text_simple function."""

    def test_simple_html(self):
        """Test extraction from simple HTML."""
        html = "<html><body><p>Hello World</p></body></html>"
        result = extract_text_simple(html)
        assert "Hello World" in result

    def test_remove_script_tags(self):
        """Test that script tags are removed."""
        html = """
        <html>
            <body>
                <p>Content</p>
                <script>alert('hello');</script>
            </body>
        </html>
        """
        result = extract_text_simple(html)
        assert "Content" in result
        assert "alert" not in result

    def test_remove_style_tags(self):
        """Test that style tags are removed."""
        html = """
        <html>
            <body>
                <p>Content</p>
                <style>body { color: red; }</style>
            </body>
        </html>
        """
        result = extract_text_simple(html)
        assert "Content" in result
        assert "color: red" not in result

    def test_html_entities(self):
        """Test extraction with HTML entities."""
        html = "<p>AT&amp;T &lt;Company&gt; &quot;test&quot;</p>"
        result = extract_text_simple(html)
        assert "AT&T" in result
        assert "<Company>" in result
        assert '"test"' in result

    def test_empty_html(self):
        """Test that empty HTML raises ValueError."""
        with pytest.raises(ValueError, match="HTML content cannot be empty"):
            extract_text_simple("")

    def test_none_html(self):
        """Test that None HTML raises ValueError."""
        with pytest.raises(ValueError, match="HTML content cannot be None"):
            extract_text_simple(None)

    def test_whitespace_cleanup(self):
        """Test that whitespace is cleaned up."""
        html = """
        <html>
            <body>
                <p>Line 1</p>


                <p>Line 2</p>
            </body>
        </html>
        """
        result = extract_text_simple(html)
        # Should have single spaces instead of multiple
        assert "  " not in result
        assert "Line 1" in result
        assert "Line 2" in result


class TestComparison:
    """Test comparing both extraction methods."""

    def test_both_methods_extract_text(self):
        """Test that both methods extract basic text correctly."""
        html = "<html><body><p>Test content</p></body></html>"
        result1 = extract_text(html)
        result2 = extract_text_simple(html)
        assert "Test content" in result1
        assert "Test content" in result2

    def test_both_remove_tags(self):
        """Test that both methods remove HTML tags."""
        html = "<p>Test <strong>bold</strong> text</p>"
        result1 = extract_text(html)
        result2 = extract_text_simple(html)
        assert "<strong>" not in result1
        assert "<strong>" not in result2
        assert "Test" in result1
        assert "bold" in result1
        assert "text" in result1
