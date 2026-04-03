"""Tests for compare_address_full_tool.

Tests cover the three additions over compare_address_tool:
  1. Kanji numeral normalization (一→1, 十一→11, …)
  2. Banchi notation normalization (1丁目2番3号 ↔ 1-2-3)
  3. Prefix/containment matching (partial addresses still match)

Plus regression coverage for the base behaviour inherited from
compare_address_tool (zenkaku/hankaku, whitespace, case, exact match).
"""

import pytest
from compare_address_full_tool import (
    normalize_address,
    compare_addresses,
    get_normalized_diff,
)


# ===========================================================================
# 1. normalize_address — base behaviour (same as compare_address_tool)
# ===========================================================================

class TestNormalizeBase:
    """Inherited normalization behaviour unchanged from compare_address_tool."""

    def test_removes_spaces(self):
        assert normalize_address("東京都 渋谷区") == "東京都渋谷区"

    def test_removes_fullwidth_space(self):
        assert normalize_address("東京都　渋谷区") == "東京都渋谷区"

    def test_removes_tabs_and_newlines(self):
        assert normalize_address("東京都\t渋谷区\n恵比寿") == "東京都渋谷区恵比寿"

    def test_fullwidth_digits_to_halfwidth(self):
        # NFKC: １２３ → 123
        assert normalize_address("渋谷区１２３") == "渋谷区123"

    def test_fullwidth_hyphen_to_halfwidth(self):
        # NFKC: － → -, U+2212 → -
        assert normalize_address("東京都渋谷区１－２－３") == "東京都渋谷区1-2-3"

    def test_fullwidth_parentheses(self):
        assert normalize_address("渋谷区（恵比寿）") == "渋谷区(恵比寿)"

    def test_lowercase(self):
        assert normalize_address("ＡＢＣ１２３") == "abc123"

    def test_empty_string(self):
        assert normalize_address("") == ""

    def test_type_error(self):
        with pytest.raises(TypeError, match="Address must be a string"):
            normalize_address(None)


# ===========================================================================
# 2. normalize_address — kanji numeral normalization
# ===========================================================================

class TestNormalizeKanjiNumerals:
    """Kanji → Arabic numeral conversion."""

    def test_single_digit(self):
        assert normalize_address("一丁目") == "1丁目"

    def test_all_single_digits(self):
        for kanji, arabic in zip("一二三四五六七八九", "123456789"):
            result = normalize_address(f"{kanji}番地")
            assert result == f"{arabic}"  # 番地 stripped by banchi normalizer

    def test_juu_alone(self):
        assert normalize_address("十丁目") == "10丁目"

    def test_compound_juu_ichi(self):
        assert normalize_address("十一丁目") == "11丁目"

    def test_compound_niju(self):
        assert normalize_address("二十丁目") == "20丁目"

    def test_compound_niju_san(self):
        assert normalize_address("二十三番地") == "23"

    def test_hyaku(self):
        assert normalize_address("百番地") == "100"

    def test_compound_address(self):
        # 一丁目二番三号 → after kanji norm → 1丁目2番3号 → after banchi → 1-2-3
        assert normalize_address("東京都渋谷区道玄坂一丁目二番三号") == "東京都渋谷区道玄坂1-2-3"

    def test_mixed_kanji_arabic(self):
        # 1丁目二番3号 → 1-2-3
        assert normalize_address("東京都渋谷区道玄坂1丁目二番3号") == "東京都渋谷区道玄坂1-2-3"


# ===========================================================================
# 3. normalize_address — banchi notation normalization
# ===========================================================================

class TestNormalizeBanchi:
    """丁目/番地/号 → hyphenated normalization."""

    def test_choume_banchi_go_full(self):
        assert normalize_address("道玄坂1丁目2番3号") == "道玄坂1-2-3"

    def test_choume_banchichi_go(self):
        # 番地 (with 地)
        assert normalize_address("道玄坂1丁目2番地3号") == "道玄坂1-2-3"

    def test_choume_hyphenated_suffix(self):
        # extractor output: 1丁目2-3
        assert normalize_address("道玄坂1丁目2-3") == "道玄坂1-2-3"

    def test_choume_banchi_no_go(self):
        assert normalize_address("道玄坂1丁目2番地") == "道玄坂1-2"

    def test_choume_ban_no_chi_no_go(self):
        # 番 without 地
        assert normalize_address("道玄坂1丁目2番") == "道玄坂1-2"

    def test_banchi_go_no_choume(self):
        assert normalize_address("山下町1番3号") == "山下町1-3"

    def test_banchi_only(self):
        assert normalize_address("山下町1番地") == "山下町1"

    def test_banchi_no_chi(self):
        assert normalize_address("山下町1番") == "山下町1"

    def test_choume_alone_unchanged(self):
        # 1丁目 without following banchi: keep as-is
        assert normalize_address("渋谷一丁目") == "渋谷1丁目"

    def test_fullwidth_before_banchi(self):
        # NFKC first, then banchi
        assert normalize_address("道玄坂１丁目２番３号") == "道玄坂1-2-3"

    def test_kanji_then_banchi(self):
        assert normalize_address("道玄坂一丁目二番三号") == "道玄坂1-2-3"


# ===========================================================================
# 4. compare_addresses — prefix/containment matching
# ===========================================================================

class TestComparePrefixMatching:
    """Prefix/containment matching: the key new behaviour."""

    def test_exact_match(self):
        assert compare_addresses("東京都渋谷区道玄坂1丁目2番3号",
                                  "東京都渋谷区道玄坂1丁目2番3号") is True

    def test_target_longer_page_is_prefix(self):
        """Page has only city-level address → should match."""
        assert compare_addresses("東京都渋谷区道玄坂1丁目2番3号",
                                  "東京都渋谷区") is True

    def test_target_shorter_page_has_more_detail(self):
        """Target has only city-level, page has full address → should match."""
        assert compare_addresses("東京都渋谷区",
                                  "東京都渋谷区道玄坂1丁目2番3号") is True

    def test_different_wards_no_match(self):
        assert compare_addresses("東京都渋谷区道玄坂1丁目2番3号",
                                  "東京都新宿区西新宿2-8-1") is False

    def test_different_prefectures_no_match(self):
        assert compare_addresses("東京都渋谷区", "大阪府大阪市北区") is False

    def test_same_city_different_ward(self):
        assert compare_addresses("大阪府大阪市北区", "大阪府大阪市中央区") is False

    def test_empty_strings(self):
        assert compare_addresses("", "") is True

    def test_empty_vs_nonempty(self):
        # Empty string is a prefix of everything
        assert compare_addresses("", "東京都渋谷区") is True


# ===========================================================================
# 5. compare_addresses — notation equivalence
# ===========================================================================

class TestCompareNotationEquivalence:
    """Different notations for the same address must compare equal."""

    def test_kanji_vs_arabic(self):
        assert compare_addresses("東京都渋谷区道玄坂一丁目二番三号",
                                  "東京都渋谷区道玄坂1丁目2番3号") is True

    def test_banchi_vs_hyphen(self):
        assert compare_addresses("東京都渋谷区道玄坂1丁目2番3号",
                                  "東京都渋谷区道玄坂1-2-3") is True

    def test_choume_hyphen_vs_banchi(self):
        assert compare_addresses("東京都渋谷区道玄坂1丁目2-3",
                                  "東京都渋谷区道玄坂1丁目2番3号") is True

    def test_fullwidth_vs_halfwidth(self):
        assert compare_addresses("東京都新宿区西新宿２－８－１",
                                  "東京都新宿区西新宿2-8-1") is True

    def test_kanji_full_vs_hyphen(self):
        assert compare_addresses("東京都渋谷区道玄坂一丁目二番三号",
                                  "東京都渋谷区道玄坂1-2-3") is True

    def test_banchi_vs_hyphen_no_choume(self):
        assert compare_addresses("神奈川県横浜市中区山下町1番地",
                                  "神奈川県横浜市中区山下町1") is True

    def test_city_ward_banchi(self):
        assert compare_addresses("大阪府大阪市北区梅田2-4-9",
                                  "大阪府大阪市北区梅田2丁目4番9号") is True

    def test_whitespace_ignored(self):
        assert compare_addresses("東京都 渋谷区　道玄坂 1丁目2番3号",
                                  "東京都渋谷区道玄坂1-2-3") is True


# ===========================================================================
# 6. get_normalized_diff — match_type field
# ===========================================================================

class TestGetNormalizedDiff:
    """Detailed comparison including match_type."""

    def test_exact_match_type(self):
        result = get_normalized_diff("東京都渋谷区", "東京都渋谷区")
        assert result['equal'] is True
        assert result['match_type'] == 'exact'

    def test_address2_is_prefix_type(self):
        result = get_normalized_diff("東京都渋谷区道玄坂1-2-3", "東京都渋谷区")
        assert result['equal'] is True
        assert result['match_type'] == 'address2_is_prefix'

    def test_address1_is_prefix_type(self):
        result = get_normalized_diff("東京都渋谷区", "東京都渋谷区道玄坂1-2-3")
        assert result['equal'] is True
        assert result['match_type'] == 'address1_is_prefix'

    def test_no_match_type(self):
        result = get_normalized_diff("東京都渋谷区", "大阪府大阪市")
        assert result['equal'] is False
        assert result['match_type'] == 'no_match'

    def test_all_keys_present(self):
        result = get_normalized_diff("addr1", "addr2")
        assert set(result.keys()) == {
            'equal', 'match_type',
            'address1_original', 'address2_original',
            'address1_normalized', 'address2_normalized',
        }

    def test_originals_preserved(self):
        a1 = "東京都　渋谷区道玄坂１丁目２番３号"
        a2 = "東京都渋谷区"
        result = get_normalized_diff(a1, a2)
        assert result['address1_original'] == a1
        assert result['address2_original'] == a2

    def test_normalized_shows_banchi_converted(self):
        result = get_normalized_diff("東京都渋谷区道玄坂1丁目2番3号", "東京都渋谷区")
        assert result['address1_normalized'] == "東京都渋谷区道玄坂1-2-3"
        assert result['address2_normalized'] == "東京都渋谷区"

    def test_normalized_shows_kanji_converted(self):
        result = get_normalized_diff("東京都渋谷区道玄坂一丁目二番三号", "x")
        assert result['address1_normalized'] == "東京都渋谷区道玄坂1-2-3"

    def test_type_error(self):
        with pytest.raises(TypeError):
            get_normalized_diff(123, "東京都")


# ===========================================================================
# 7. Real-world integration scenarios (officialsite_finder use case)
# ===========================================================================

class TestRealWorldScenarios:
    """Scenarios that arise when compare_address_full_tool is used inside
    officialsite_finder_tool: target from user input vs address extracted
    from a web page."""

    def test_full_vs_city_level(self):
        """Page extracted only prefecture+city from HTML."""
        target = "東京都渋谷区道玄坂1丁目2番3号"
        page   = "東京都渋谷区"
        assert compare_addresses(target, page) is True

    def test_full_vs_full_hyphen(self):
        """Page uses hyphenated form; target uses 丁目/番地/号 form."""
        target = "東京都新宿区西新宿2丁目8番1号"
        page   = "東京都新宿区西新宿2-8-1"
        assert compare_addresses(target, page) is True

    def test_osaka_city_ward(self):
        """Two-layer city+ward address with hyphen."""
        target = "大阪府大阪市北区梅田2丁目4番9号"
        page   = "大阪府大阪市北区梅田2-4-9"
        assert compare_addresses(target, page) is True

    def test_kanagawa_banchi(self):
        """Banchi-only address comparison."""
        target = "神奈川県横浜市中区山下町1番地"
        page   = "神奈川県横浜市中区山下町1"
        assert compare_addresses(target, page) is True

    def test_different_facility_no_match(self):
        """Two completely different facilities."""
        target = "東京都渋谷区道玄坂1丁目2番3号"
        page   = "大阪府大阪市北区梅田2-4-9"
        assert compare_addresses(target, page) is False

    def test_kanji_user_input(self):
        """User supplied address with kanji numerals."""
        target = "東京都渋谷区道玄坂一丁目二番三号"
        page   = "東京都渋谷区道玄坂1-2-3"
        assert compare_addresses(target, page) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
