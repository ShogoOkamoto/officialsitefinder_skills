"""Tests for address input variants — 東京タワー 東京都港区芝公園4丁目2番8号

Verifies that extract_full_address_tool + compare_address_full (prefix/containment)
correctly handles various input formats and still produces a match against the
canonical address as it appears on the official site.

Covers:
  A. Street-level extraction (full banchi extracted and normalized)
     - Full-width digits + U+2212 minus sign:  ４丁目２−８
     - Half-width hyphen after 丁目:            4丁目2-8
     - Standard 番地号 notation:               4丁目2番8号
     - All-hyphenated (no 丁目):               4-2-8
     - Full-width digits + full-width hyphen:  ４－２－８
     - Kanji numerals:                         四丁目二番八号
     - With 番地:                              4丁目2番地8号

  B. City-level-only extraction (street number not captured; prefix match succeeds)
     - の-separated:   4の2の8
     - Space before number: 芝公園 4-2-8
     - Kanji with の:  四の二の八
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "compare_address_full_skill"))
from compare_address_full import compare_addresses, normalize_address
from extract_full_address_tool import extract_full_addresses_list

# Address as it appears in tokyotower.co.jp/company/ HTML
CANONICAL_PAGE_ADDRESS = "東京都港区芝公園4丁目2番8号"
CANONICAL_NORMALIZED   = "東京都港区芝公園4-2-8"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_first(input_addr: str) -> str | None:
    """Return the first address extracted from input_addr, or None."""
    results = extract_full_addresses_list(input_addr)
    return results[0] if results else None


# ---------------------------------------------------------------------------
# Group A: Full street-level extraction
# Expected: extract_full_addresses_list returns a street-level address that
#           normalizes to CANONICAL_NORMALIZED, and compare_addresses → True.
# ---------------------------------------------------------------------------

STREET_LEVEL_VARIANTS = [
    ("全角＋U+2212",    "東京都港区芝公園４丁目２−８",    "東京都港区芝公園4-2-8"),
    ("半角ハイフン後",  "東京都港区芝公園4丁目2-8",       "東京都港区芝公園4-2-8"),
    ("標準番地号",      "東京都港区芝公園4丁目2番8号",    "東京都港区芝公園4-2-8"),
    ("全ハイフン",      "東京都港区芝公園4-2-8",           "東京都港区芝公園4-2-8"),
    ("全角全角ハイフン","東京都港区芝公園４－２－８",      "東京都港区芝公園4-2-8"),
    ("漢数字",          "東京都港区芝公園四丁目二番八号",  "東京都港区芝公園4-2-8"),
    ("番地あり",        "東京都港区芝公園4丁目2番地8号",   "東京都港区芝公園4-2-8"),
]


@pytest.mark.parametrize("label,input_addr,expected_norm", STREET_LEVEL_VARIANTS,
                         ids=[v[0] for v in STREET_LEVEL_VARIANTS])
class TestStreetLevelExtraction:
    """Street number is extracted and normalizes to canonical."""

    def test_extract_returns_result(self, label, input_addr, expected_norm):
        """extract_full_addresses_list returns at least one address."""
        result = _extract_first(input_addr)
        assert result is not None, f"[{label}] No address extracted from: {input_addr}"

    def test_normalized_form(self, label, input_addr, expected_norm):
        """Normalized form matches the canonical normalized address."""
        result = _extract_first(input_addr)
        assert result is not None
        assert normalize_address(result) == expected_norm, (
            f"[{label}] normalize({result!r}) = {normalize_address(result)!r} "
            f"!= {expected_norm!r}"
        )

    def test_matches_canonical_page_address(self, label, input_addr, expected_norm):
        """compare_addresses returns True against the canonical page address."""
        result = _extract_first(input_addr)
        assert result is not None
        assert compare_addresses(result, CANONICAL_PAGE_ADDRESS), (
            f"[{label}] compare_addresses({result!r}, {CANONICAL_PAGE_ADDRESS!r}) = False"
        )


# ---------------------------------------------------------------------------
# Group B: City-level-only extraction (街番地が取れないが前方一致で合格)
# Expected: extract returns city-level address, compare_addresses → True
#           via prefix/containment matching.
# ---------------------------------------------------------------------------

CITY_LEVEL_VARIANTS = [
    ("の区切り",    "東京都港区芝公園4の2の8",   "東京都港区"),
    ("スペース前",  "東京都港区芝公園 4-2-8",    "東京都港区"),
    ("四の二の八",  "東京都港区芝公園四の二の八", "東京都港区"),
]


@pytest.mark.parametrize("label,input_addr,expected_prefix", CITY_LEVEL_VARIANTS,
                         ids=[v[0] for v in CITY_LEVEL_VARIANTS])
class TestCityLevelPrefixMatch:
    """Street number not extracted; matches page address via prefix containment."""

    def test_extract_returns_result(self, label, input_addr, expected_prefix):
        """extract_full_addresses_list returns at least one address."""
        result = _extract_first(input_addr)
        assert result is not None, f"[{label}] No address extracted from: {input_addr}"

    def test_extracted_at_city_level(self, label, input_addr, expected_prefix):
        """Extracted address is at city level (not street level)."""
        result = _extract_first(input_addr)
        assert result is not None
        assert normalize_address(result) == normalize_address(expected_prefix), (
            f"[{label}] Expected city-level {expected_prefix!r}, got {result!r}"
        )

    def test_matches_canonical_via_prefix(self, label, input_addr, expected_prefix):
        """compare_addresses returns True via prefix/containment matching."""
        result = _extract_first(input_addr)
        assert result is not None
        assert compare_addresses(result, CANONICAL_PAGE_ADDRESS), (
            f"[{label}] compare_addresses({result!r}, {CANONICAL_PAGE_ADDRESS!r}) = False"
        )


# ---------------------------------------------------------------------------
# Normalization unit tests — verify normalize_address independently
# ---------------------------------------------------------------------------

class TestNormalizeAddress:
    """normalize_address converts all variants to the same canonical form."""

    @pytest.mark.parametrize("input_addr,expected", [
        ("東京都港区芝公園４丁目２−８",    "東京都港区芝公園4-2-8"),
        ("東京都港区芝公園4丁目2-8",       "東京都港区芝公園4-2-8"),
        ("東京都港区芝公園4丁目2番8号",    "東京都港区芝公園4-2-8"),
        ("東京都港区芝公園4-2-8",           "東京都港区芝公園4-2-8"),
        ("東京都港区芝公園４－２－８",      "東京都港区芝公園4-2-8"),
        ("東京都港区芝公園四丁目二番八号",  "東京都港区芝公園4-2-8"),
        ("東京都港区芝公園4丁目2番地8号",   "東京都港区芝公園4-2-8"),
        ("東京都港区芝公園4丁目2番8号",     "東京都港区芝公園4-2-8"),  # canonical itself
    ])
    def test_normalizes_to_canonical(self, input_addr, expected):
        assert normalize_address(input_addr) == expected, (
            f"normalize({input_addr!r}) = {normalize_address(input_addr)!r} != {expected!r}"
        )


# ---------------------------------------------------------------------------
# compare_addresses cross-variant tests
# All street-level variants should match each other
# ---------------------------------------------------------------------------

class TestCrossVariantComparison:
    """All street-level variants should compare equal to each other."""

    @pytest.mark.parametrize("addr1", [v[1] for v in STREET_LEVEL_VARIANTS],
                             ids=[v[0] for v in STREET_LEVEL_VARIANTS])
    @pytest.mark.parametrize("addr2", [v[1] for v in STREET_LEVEL_VARIANTS],
                             ids=[v[0] for v in STREET_LEVEL_VARIANTS])
    def test_street_variants_match_each_other(self, addr1, addr2):
        """Any two street-level variants should compare as equal."""
        # Extract first, then compare (simulating the pipeline)
        ext1 = _extract_first(addr1)
        ext2 = _extract_first(addr2)
        assert ext1 is not None and ext2 is not None
        assert compare_addresses(ext1, ext2), (
            f"compare_addresses({ext1!r}, {ext2!r}) = False"
        )


# ---------------------------------------------------------------------------
# Group C: Extraction failure — no prefecture prefix
# Expected: extract_full_addresses_list returns [] and the pipeline would
#           output success: false / "住所の抽出に失敗しました".
# ---------------------------------------------------------------------------

EXTRACTION_FAILURE_VARIANTS = [
    ("港区のみ",   "港区"),
    ("芝公園のみ", "芝公園"),
    ("番地のみ",   "4-2-8"),
    ("空文字",     ""),
]


@pytest.mark.parametrize("label,input_addr", EXTRACTION_FAILURE_VARIANTS,
                         ids=[v[0] for v in EXTRACTION_FAILURE_VARIANTS])
class TestExtractionFailure:
    """Addresses without a prefecture prefix cannot be extracted.

    These inputs return an empty list from extract_full_addresses_list,
    which causes the pipeline to output success: false.
    """

    def test_extract_returns_empty(self, label, input_addr):
        """No address is extracted — pipeline would fail at Step 2."""
        result = extract_full_addresses_list(input_addr)
        assert result == [], (
            f"[{label}] Expected empty list for {input_addr!r}, got {result!r}"
        )

    def test_no_match_against_canonical(self, label, input_addr):
        """Without extraction, comparison is not attempted (no false positives)."""
        result = extract_full_addresses_list(input_addr)
        # Verify there is nothing to compare — prevents accidental prefix matches
        assert len(result) == 0, (
            f"[{label}] Should not extract anything from {input_addr!r}"
        )
