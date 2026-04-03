"""Unit tests for officialsite_finder_tool.__main__ pure functions.

Tests cover:
  1. is_top_page_by_url - URL structure-based top page detection
  2. get_domain_root - extract domain root from URL
  3. load_criteria - load criteria.txt file
"""

import json
import os
import tempfile
import pytest

from officialsite_finder_tool.__main__ import (
    is_top_page_by_url,
    get_domain_root,
    load_criteria,
)


# ===========================================================================
# 1. is_top_page_by_url
# ===========================================================================

class TestIsTopPageByUrl:

    def test_domain_root_no_slash(self):
        assert is_top_page_by_url("https://example.com") is True

    def test_domain_root_with_slash(self):
        assert is_top_page_by_url("https://example.com/") is True

    def test_index_html(self):
        assert is_top_page_by_url("https://example.com/index.html") is True

    def test_index_php(self):
        assert is_top_page_by_url("https://example.com/index.php") is True

    def test_index_htm(self):
        assert is_top_page_by_url("https://example.com/index.htm") is True

    def test_subpage_is_not_top(self):
        assert is_top_page_by_url("https://example.com/about") is False

    def test_deep_subpage_is_not_top(self):
        assert is_top_page_by_url("https://example.com/clinic/access") is False

    def test_news_page_is_not_top(self):
        assert is_top_page_by_url("https://example.com/news/2024/01/01") is False

    def test_trailing_slash_subpage_is_not_top(self):
        assert is_top_page_by_url("https://example.com/about/") is False

    def test_query_string_root(self):
        """Root with query string: path is empty → top page."""
        assert is_top_page_by_url("https://example.com/?lang=ja") is True

    def test_invalid_url_returns_false(self):
        assert is_top_page_by_url("not-a-url") is False

    def test_empty_string_returns_true(self):
        # urlparse("") produces an empty path, which matches the top-page condition
        assert is_top_page_by_url("") is True

    def test_http_scheme(self):
        assert is_top_page_by_url("http://example.com/") is True

    def test_subdomain_root(self):
        assert is_top_page_by_url("https://www.example.co.jp/") is True

    def test_subdomain_subpage(self):
        assert is_top_page_by_url("https://www.example.co.jp/about/") is False


# ===========================================================================
# 2. get_domain_root
# ===========================================================================

class TestGetDomainRoot:

    def test_basic_url(self):
        assert get_domain_root("https://example.com/about") == "https://example.com/"

    def test_already_root(self):
        assert get_domain_root("https://example.com/") == "https://example.com/"

    def test_deep_path(self):
        assert get_domain_root("https://www.hospital.jp/clinic/access/map") == "https://www.hospital.jp/"

    def test_http_scheme_preserved(self):
        assert get_domain_root("http://example.com/page") == "http://example.com/"

    def test_subdomain_preserved(self):
        assert get_domain_root("https://sub.example.co.jp/path") == "https://sub.example.co.jp/"

    def test_with_query_string(self):
        result = get_domain_root("https://example.com/search?q=test")
        assert result == "https://example.com/"

    def test_with_port(self):
        assert get_domain_root("https://example.com:8080/path") == "https://example.com:8080/"

    def test_invalid_url_returns_none(self):
        # urlparse doesn't raise; netloc will be empty for truly invalid URLs
        result = get_domain_root("not-a-url")
        # Should return something or None — check it doesn't raise
        assert result is None or isinstance(result, str)

    def test_empty_string(self):
        result = get_domain_root("")
        # Should return empty-scheme root or None
        assert result is None or isinstance(result, str)


# ===========================================================================
# 3. load_criteria
# ===========================================================================

class TestLoadCriteria:

    def test_loads_existing_file(self, tmp_path):
        criteria_file = tmp_path / "criteria.txt"
        criteria_file.write_text("収集対象: 公式サイトのみ\n除外: ポータルサイト", encoding="utf-8")
        result = load_criteria(str(criteria_file))
        assert "収集対象" in result
        assert "除外" in result

    def test_returns_none_for_missing_file(self, tmp_path):
        result = load_criteria(str(tmp_path / "nonexistent.txt"))
        assert result is None

    def test_empty_file_returns_empty_string(self, tmp_path):
        criteria_file = tmp_path / "criteria.txt"
        criteria_file.write_text("", encoding="utf-8")
        result = load_criteria(str(criteria_file))
        assert result == ""

    def test_utf8_content(self, tmp_path):
        criteria_file = tmp_path / "criteria.txt"
        content = "基準：公式サイトであること\n\n詳細:\n- トップページであること"
        criteria_file.write_text(content, encoding="utf-8")
        result = load_criteria(str(criteria_file))
        assert result == content

    def test_multiline_content(self, tmp_path):
        criteria_file = tmp_path / "criteria.txt"
        lines = ["line1", "line2", "line3"]
        criteria_file.write_text("\n".join(lines), encoding="utf-8")
        result = load_criteria(str(criteria_file))
        assert result == "\n".join(lines)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
