"""
compare_address_full_tool - Japanese Full Address Comparison Tool

Compares Japanese addresses including block/lot numbers (丁目・番地・号),
normalizing:
  - Full-width / half-width character differences (NFKC)
  - Whitespace differences
  - Kanji numeral vs Arabic numeral (一→1, 十一→11, ...)
  - Banchi notation vs hyphenated notation (1丁目2番3号 ↔ 1-2-3)

Matching strategy: prefix/containment matching.
One address is considered a match if it is equal to, or a prefix of, the other
after normalization.  This handles the common case where a web page carries only
the prefecture+city portion of an address while the facility's full street-level
address is known.
"""

import re
import unicodedata
from typing import Literal


# ---------------------------------------------------------------------------
# Kanji numeral conversion
# ---------------------------------------------------------------------------

_KANJI_DIGIT: dict[str, int] = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9,
}
_KANJI_MAG: dict[str, int] = {'十': 10, '百': 100, '千': 1000}
_KANJI_NUM_RE = re.compile(r'[一二三四五六七八九十百千]+')


def _kanji_to_int(s: str) -> int:
    """Convert a kanji numeral string to an integer.

    Examples:
        '一' → 1, '十一' → 11, '二十三' → 23, '百五十' → 150
    """
    total = 0
    current = 0
    for ch in s:
        if ch in _KANJI_DIGIT:
            current = _KANJI_DIGIT[ch]
        elif ch in _KANJI_MAG:
            mag = _KANJI_MAG[ch]
            total += (current if current else 1) * mag
            current = 0
    total += current
    return total


def _normalize_kanji_numbers(text: str) -> str:
    """Replace kanji numeral sequences in *text* with Arabic numerals."""
    return _KANJI_NUM_RE.sub(lambda m: str(_kanji_to_int(m.group(0))), text)


# ---------------------------------------------------------------------------
# Banchi notation normalization (丁目/番地/号 → hyphenated)
# ---------------------------------------------------------------------------

# Apply patterns from most specific to least specific.
_BANCHI_PATTERNS = [
    # 1丁目2番地3号 / 1丁目2番3号 → 1-2-3
    (re.compile(r'(\d+)丁目(\d+)番地?(\d+)号'), r'\1-\2-\3'),
    # 1丁目2-3 (丁目 then already-hyphenated part) → 1-2-3
    (re.compile(r'(\d+)丁目(\d+)-(\d+)'), r'\1-\2-\3'),
    # 1丁目2番地 / 1丁目2番 (no 号) → 1-2
    (re.compile(r'(\d+)丁目(\d+)番地?'), r'\1-\2'),
    # 2番地3号 / 2番3号 (no 丁目) → 2-3
    (re.compile(r'(\d+)番地?(\d+)号'), r'\1-\2'),
    # 1番地 / 1番 (banchi only) → 1
    (re.compile(r'(\d+)番地?'), r'\1'),
]


def _normalize_banchi(text: str) -> str:
    """Unify 丁目/番地/号 notation to hyphenated form."""
    for pattern, replacement in _BANCHI_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_address(address: str) -> str:
    """
    Normalize a Japanese full address for comparison.

    Normalization steps:
    1. Remove all whitespace (including full-width spaces)
    2. NFKC normalization (full-width → half-width, etc.)
    3. Replace U+2212 MINUS SIGN with U+002D HYPHEN-MINUS
    4. Convert kanji numerals to Arabic (一→1, 十一→11, …)
    5. Convert 丁目/番地/号 notation to hyphenated form (1丁目2番3号→1-2-3)
    6. Lowercase

    Args:
        address: The address string to normalize.

    Returns:
        Normalized address string.

    Examples:
        >>> normalize_address("東京都　渋谷区道玄坂１丁目２番３号")
        '東京都渋谷区道玄坂1-2-3'
        >>> normalize_address("東京都渋谷区道玄坂一丁目二番三号")
        '東京都渋谷区道玄坂1-2-3'
    """
    if not isinstance(address, str):
        raise TypeError(f"Address must be a string, got {type(address).__name__}")

    # 1. Remove whitespace (including ideographic space U+3000)
    normalized = ''.join(address.split())

    # 2. NFKC: full-width → half-width, katakana normalization, etc.
    normalized = unicodedata.normalize('NFKC', normalized)

    # 3. U+2212 MINUS SIGN → hyphen-minus
    normalized = normalized.replace('\u2212', '-')

    # 4. Kanji numerals → Arabic
    normalized = _normalize_kanji_numbers(normalized)

    # 5. 丁目/番地/号 → hyphenated
    normalized = _normalize_banchi(normalized)

    # 6. Lowercase
    normalized = normalized.lower()

    return normalized


MatchType = Literal['exact', 'address1_is_prefix', 'address2_is_prefix', 'no_match']


def compare_addresses(address1: str, address2: str) -> bool:
    """
    Compare two Japanese addresses using prefix/containment matching.

    Returns True when:
    - The normalized addresses are identical (exact match), OR
    - address1 is a prefix of address2 (address1 has less detail), OR
    - address2 is a prefix of address1 (address2 has less detail)

    This handles the common scenario where a web page only carries a
    prefecture+city address while the target has a full street-level address.

    Args:
        address1: First address to compare.
        address2: Second address to compare.

    Returns:
        True if the addresses are compatible, False otherwise.

    Examples:
        >>> compare_addresses("東京都渋谷区道玄坂1丁目2番3号", "東京都渋谷区道玄坂1-2-3")
        True
        >>> compare_addresses("東京都渋谷区道玄坂1丁目2番3号", "東京都渋谷区")
        True
        >>> compare_addresses("東京都渋谷区", "大阪府大阪市北区")
        False
    """
    if not isinstance(address1, str):
        raise TypeError(f"address1 must be a string, got {type(address1).__name__}")
    if not isinstance(address2, str):
        raise TypeError(f"address2 must be a string, got {type(address2).__name__}")

    n1 = normalize_address(address1)
    n2 = normalize_address(address2)

    return n1 == n2 or n1.startswith(n2) or n2.startswith(n1)


def get_normalized_diff(address1: str, address2: str) -> dict:
    """
    Return detailed comparison information between two addresses.

    Args:
        address1: First address to compare.
        address2: Second address to compare.

    Returns:
        Dictionary containing:
        - 'equal':               bool — True if addresses are compatible
        - 'match_type':          str  — 'exact' | 'address1_is_prefix' |
                                        'address2_is_prefix' | 'no_match'
        - 'address1_original':   str  — Original first address
        - 'address2_original':   str  — Original second address
        - 'address1_normalized': str  — Normalized first address
        - 'address2_normalized': str  — Normalized second address

    Examples:
        >>> r = get_normalized_diff("東京都渋谷区道玄坂1丁目2番3号", "東京都渋谷区")
        >>> r['equal']
        True
        >>> r['match_type']
        'address2_is_prefix'
    """
    n1 = normalize_address(address1)
    n2 = normalize_address(address2)

    if n1 == n2:
        match_type: MatchType = 'exact'
    elif n1.startswith(n2):
        match_type = 'address2_is_prefix'
    elif n2.startswith(n1):
        match_type = 'address1_is_prefix'
    else:
        match_type = 'no_match'

    return {
        'equal': match_type != 'no_match',
        'match_type': match_type,
        'address1_original': address1,
        'address2_original': address2,
        'address1_normalized': n1,
        'address2_normalized': n2,
    }


__all__ = ['normalize_address', 'compare_addresses', 'get_normalized_diff']
