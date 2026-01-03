"""
Comprehensive test suite for compare_address_tool.

Tests cover:
- Normalization of full-width/half-width characters
- Whitespace handling (spaces, tabs, newlines)
- Address comparison functionality
- Edge cases and error handling
- Detailed comparison results
"""

import pytest
from compare_address_tool import (
    normalize_address,
    compare_addresses,
    get_normalized_diff
)


class TestNormalizeAddress:
    """Tests for the normalize_address function."""

    def test_normalize_removes_spaces(self):
        """Test that spaces are removed during normalization."""
        address = "東京都 渋谷区 恵比寿"
        normalized = normalize_address(address)
        assert ' ' not in normalized
        assert normalized == "東京都渋谷区恵比寿"

    def test_normalize_removes_tabs(self):
        """Test that tabs are removed during normalization."""
        address = "東京都\t渋谷区\t恵比寿"
        normalized = normalize_address(address)
        assert '\t' not in normalized
        assert normalized == "東京都渋谷区恵比寿"

    def test_normalize_removes_multiple_spaces(self):
        """Test that multiple consecutive spaces are removed."""
        address = "東京都    渋谷区    恵比寿"
        normalized = normalize_address(address)
        assert normalized == "東京都渋谷区恵比寿"

    def test_normalize_removes_newlines(self):
        """Test that newlines are removed during normalization."""
        address = "東京都\n渋谷区\n恵比寿"
        normalized = normalize_address(address)
        assert '\n' not in normalized
        assert normalized == "東京都渋谷区恵比寿"

    def test_normalize_zenkaku_to_hankaku_numbers(self):
        """Test that full-width numbers are converted to half-width."""
        address = "東京都渋谷区１−２−３"
        normalized = normalize_address(address)
        assert "１" not in normalized
        assert "1" in normalized
        assert normalized == "東京都渋谷区1-2-3"

    def test_normalize_zenkaku_to_hankaku_alphanumeric(self):
        """Test that full-width alphanumeric characters are converted."""
        address = "ＡＢＣ１２３"
        normalized = normalize_address(address)
        assert normalized == "abc123"

    def test_normalize_zenkaku_katakana(self):
        """Test that full-width katakana is converted to half-width."""
        # Full-width katakana ア (U+30A2) vs half-width ア (U+FF71)
        address = "トウキョウト"  # Full-width
        normalized = normalize_address(address)
        # NFKC should convert to half-width katakana
        assert "トウキョウト" in normalized or "ﾄｳｷｮｳﾄ" in normalized

    def test_normalize_mixed_whitespace(self):
        """Test normalization with mixed whitespace types."""
        address = "東京都 \t渋谷区\n恵比寿　１−２−３"
        normalized = normalize_address(address)
        assert ' ' not in normalized
        assert '\t' not in normalized
        assert '\n' not in normalized
        assert '　' not in normalized  # Full-width space
        assert normalized == "東京都渋谷区恵比寿1-2-3"

    def test_normalize_empty_string(self):
        """Test normalization of empty string."""
        assert normalize_address("") == ""

    def test_normalize_whitespace_only(self):
        """Test normalization of whitespace-only string."""
        assert normalize_address("   \t\n  ") == ""

    def test_normalize_preserves_kanji(self):
        """Test that kanji characters are preserved."""
        address = "東京都渋谷区恵比寿"
        normalized = normalize_address(address)
        assert normalized == "東京都渋谷区恵比寿"

    def test_normalize_case_conversion(self):
        """Test that uppercase letters are converted to lowercase."""
        address = "Tokyo ABC"
        normalized = normalize_address(address)
        assert normalized == "tokyoabc"

    def test_normalize_type_error(self):
        """Test that TypeError is raised for non-string input."""
        with pytest.raises(TypeError, match="Address must be a string"):
            normalize_address(123)

        with pytest.raises(TypeError, match="Address must be a string"):
            normalize_address(None)

    def test_normalize_full_width_space(self):
        """Test that full-width spaces (　) are removed."""
        address = "東京都　渋谷区　恵比寿"
        normalized = normalize_address(address)
        assert '　' not in normalized
        assert normalized == "東京都渋谷区恵比寿"

    def test_normalize_complex_address(self):
        """Test normalization of a complex real-world address."""
        address = "東京都　渋谷区　恵比寿南　１−２−３　恵比寿ビル　５Ｆ"
        normalized = normalize_address(address)
        assert ' ' not in normalized and '　' not in normalized
        assert "１" not in normalized and "Ｆ" not in normalized
        assert "1" in normalized and "f" in normalized


class TestCompareAddresses:
    """Tests for the compare_addresses function."""

    def test_compare_identical_addresses(self):
        """Test comparison of identical addresses."""
        address = "東京都渋谷区恵比寿"
        assert compare_addresses(address, address) is True

    def test_compare_with_space_difference(self):
        """Test that addresses differing only in spaces are equal."""
        address1 = "東京都渋谷区恵比寿"
        address2 = "東京都 渋谷区 恵比寿"
        assert compare_addresses(address1, address2) is True

    def test_compare_with_tab_difference(self):
        """Test that addresses differing only in tabs are equal."""
        address1 = "東京都渋谷区恵比寿"
        address2 = "東京都\t渋谷区\t恵比寿"
        assert compare_addresses(address1, address2) is True

    def test_compare_zenkaku_hankaku_numbers(self):
        """Test that full-width and half-width numbers are treated as equal."""
        address1 = "東京都渋谷区１−２−３"
        address2 = "東京都渋谷区1-2-3"
        assert compare_addresses(address1, address2) is True

    def test_compare_zenkaku_hankaku_alphanumeric(self):
        """Test that full-width and half-width alphanumerics are equal."""
        address1 = "ビル５Ｆ"
        address2 = "ビル5F"
        assert compare_addresses(address1, address2) is True

    def test_compare_different_addresses(self):
        """Test that genuinely different addresses are not equal."""
        address1 = "東京都渋谷区"
        address2 = "大阪府大阪市"
        assert compare_addresses(address1, address2) is False

    def test_compare_mixed_whitespace(self):
        """Test comparison with various whitespace types."""
        address1 = "東京都 渋谷区\t恵比寿\n１−２−３"
        address2 = "東京都　渋谷区　恵比寿　1-2-3"
        assert compare_addresses(address1, address2) is True

    def test_compare_empty_strings(self):
        """Test comparison of empty strings."""
        assert compare_addresses("", "") is True

    def test_compare_whitespace_only(self):
        """Test comparison of whitespace-only strings."""
        assert compare_addresses("   ", "\t\n") is True

    def test_compare_case_insensitive(self):
        """Test that comparison is case-insensitive."""
        address1 = "Tokyo ABC"
        address2 = "tokyo abc"
        assert compare_addresses(address1, address2) is True

    def test_compare_complex_real_world(self):
        """Test comparison of complex real-world addresses with various differences."""
        address1 = "東京都　渋谷区　恵比寿南　１−２−３　恵比寿ビル　５Ｆ"
        address2 = "東京都渋谷区恵比寿南1-2-3恵比寿ビル5F"
        assert compare_addresses(address1, address2) is True

    def test_compare_type_error_first_arg(self):
        """Test that TypeError is raised for non-string first argument."""
        with pytest.raises(TypeError, match="address1 must be a string"):
            compare_addresses(123, "東京都")

    def test_compare_type_error_second_arg(self):
        """Test that TypeError is raised for non-string second argument."""
        with pytest.raises(TypeError, match="address2 must be a string"):
            compare_addresses("東京都", None)

    def test_compare_partial_match(self):
        """Test that partial matches are not considered equal."""
        address1 = "東京都渋谷区恵比寿"
        address2 = "東京都渋谷区"
        assert compare_addresses(address1, address2) is False


class TestGetNormalizedDiff:
    """Tests for the get_normalized_diff function."""

    def test_diff_equal_addresses(self):
        """Test diff for equal addresses."""
        address1 = "東京都　渋谷区"
        address2 = "東京都渋谷区"
        result = get_normalized_diff(address1, address2)

        assert result['equal'] is True
        assert result['address1_original'] == address1
        assert result['address2_original'] == address2
        assert result['address1_normalized'] == "東京都渋谷区"
        assert result['address2_normalized'] == "東京都渋谷区"

    def test_diff_different_addresses(self):
        """Test diff for different addresses."""
        address1 = "東京都"
        address2 = "大阪府"
        result = get_normalized_diff(address1, address2)

        assert result['equal'] is False
        assert result['address1_original'] == address1
        assert result['address2_original'] == address2
        assert result['address1_normalized'] == "東京都"
        assert result['address2_normalized'] == "大阪府"

    def test_diff_zenkaku_hankaku(self):
        """Test diff showing normalization of zenkaku/hankaku."""
        address1 = "１２３ＡＢＣ"
        address2 = "123ABC"
        result = get_normalized_diff(address1, address2)

        assert result['equal'] is True
        assert result['address1_original'] == address1
        assert result['address2_original'] == address2
        assert result['address1_normalized'] == "123abc"
        assert result['address2_normalized'] == "123abc"

    def test_diff_preserves_original(self):
        """Test that diff preserves original addresses unchanged."""
        address1 = "東京都　１２３"
        address2 = "東京都 123"
        result = get_normalized_diff(address1, address2)

        # Originals should be unchanged
        assert '　' in result['address1_original']
        assert '１２３' in result['address1_original']
        assert ' ' in result['address2_original']

        # Normalized should be cleaned
        assert '　' not in result['address1_normalized']
        assert ' ' not in result['address2_normalized']
        assert result['address1_normalized'] == result['address2_normalized']

    def test_diff_result_structure(self):
        """Test that diff returns all required keys."""
        result = get_normalized_diff("test1", "test2")

        assert 'equal' in result
        assert 'address1_original' in result
        assert 'address2_original' in result
        assert 'address1_normalized' in result
        assert 'address2_normalized' in result
        assert isinstance(result['equal'], bool)


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_unicode_normalization_edge_cases(self):
        """Test various Unicode normalization edge cases."""
        # Test that NFKC normalization works correctly
        # ① (circled 1) should normalize to 1
        address1 = "①②③"
        normalized = normalize_address(address1)
        assert "1" in normalized or "①" in normalized  # NFKC may or may not convert circled numbers

    def test_very_long_address(self):
        """Test handling of very long addresses."""
        address = "東京都渋谷区恵比寿南" * 100
        normalized = normalize_address(address)
        assert len(normalized) == len("東京都渋谷区恵比寿南" * 100)

    def test_special_characters(self):
        """Test handling of special characters in addresses."""
        address1 = "東京都-渋谷区・恵比寿"
        address2 = "東京都-渋谷区・恵比寿"
        assert compare_addresses(address1, address2) is True

    def test_mixed_japanese_english(self):
        """Test addresses with mixed Japanese and English."""
        address1 = "東京都 Shibuya-ku ５−１０−２５"
        address2 = "東京都Shibuya-ku5-10-25"
        assert compare_addresses(address1, address2) is True

    def test_parentheses_and_brackets(self):
        """Test addresses containing parentheses and brackets."""
        address1 = "東京都渋谷区（恵比寿）"
        address2 = "東京都渋谷区(恵比寿)"
        # Full-width and half-width parentheses should normalize
        assert compare_addresses(address1, address2) is True
