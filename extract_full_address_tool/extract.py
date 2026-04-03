"""Japanese full address extraction module.

This module extracts Japanese addresses including block/lot numbers
(丁目・番地・号 or hyphenated form) from plain text and returns them as JSON.
"""

import re
import json
from typing import List


# 47 prefectures in Japan
PREFECTURES = [
    "北海道",
    "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県",
    "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県",
    "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県",
    "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"
]


def _build_patterns():
    """Build regex patterns for full address extraction."""
    prefecture_pattern = '|'.join(re.escape(pref) for pref in PREFECTURES)

    # City/ward/town/village name - excludes common delimiters
    city_name = r'(?:(?!と|や|及び|、|。)[ぁ-んァ-ヶー一-龠々\d])+'

    # Number characters: half-width, full-width, and kanji numerals
    any_num = r'[0-9０-９一二三四五六七八九十百千]+'
    # Hyphens: half-width (U+002D), full-width (U+FF0D), minus sign (U+2212)
    hyph = '[-－\u2212]'
    # Town name characters (Japanese only, no digits)
    town_char = r'[ぁ-んァ-ヶー一-龠々]'

    # Banchi/go: "2番3号" or "2番地" or "2番"
    banchi_go = f'(?:{any_num}番地?(?:{any_num}号)?)'
    # Hyphenated: "1-2-3" or "1-2"
    hyphenated = f'(?:{any_num}{hyph}{any_num}(?:{hyph}{any_num})?)'
    # Choume: "1丁目", optionally followed by banchi or hyphenated suffix
    choume = f'(?:{any_num}丁目(?:{banchi_go}|{hyphenated})?)'
    # Jou-choume: Sapporo/Hokkaido style "N条M丁目" (e.g. "1条西16丁目291番地")
    jou_choume = f'(?:{any_num}条{town_char}*{any_num}丁目(?:{banchi_go}|{hyphenated})?)'

    # Street number: one of the above forms
    street_num = f'(?:{jou_choume}|{choume}|{banchi_go}|{hyphenated})'

    # Address extension: optional town-name characters + required street number
    addr_ext = f'(?:{town_char}*{street_num})'

    # Strict city/ward name for no-prefecture patterns:
    # - Must start with kanji or katakana (not hiragana particles)
    # - Excludes common particles (は/が/の/を/に/で/へ/も/か) within the name
    # - Limited to 6 chars max to prevent consuming surrounding sentence text
    _p = r'(?!は|が|の|を|に|で|へ|も|か|と|や|及び|、|。)'
    city_name_nopref = r'[ァ-ヶー一-龠々](?:' + _p + r'[ぁ-んァ-ヶー一-龠々\d]){0,5}'
    # County for no-prefecture patterns (non-capturing, optional)
    county_nopref = r'(?:[ァ-ヶー一-龠々](?:' + _p + r'[ぁ-んァ-ヶー一-龠々\d]){0,5}郡)?'
    # County for no-prefecture patterns (one capturing group, optional)
    county_nopref_cap = r'([ァ-ヶー一-龠々](?:' + _p + r'[ぁ-んァ-ヶー一-龠々\d]){0,5}郡)?'

    # Non-capturing pattern for basic extraction
    basic_pattern = (
        # With prefecture (street number optional)
        f'(?:{prefecture_pattern})(?:[^と、。\\s]*郡)?(?:{city_name})市(?:{city_name}区)?(?:{addr_ext})?'
        f'|'
        f'(?:{prefecture_pattern})(?:[^と、。\\s]*郡)?(?:{city_name})(?:区|町|村)(?:{addr_ext})?'
        f'|'
        # Without prefecture: strict city_name, street number required to avoid false positives
        f'{county_nopref}(?:{city_name_nopref})市(?:{city_name_nopref}区)?{addr_ext}'
        f'|'
        f'{county_nopref}(?:{city_name_nopref})(?:区|町|村){addr_ext}'
    )

    # Capturing pattern for detailed extraction
    # Pattern 1 groups: (1)pref (2)county (3)city_name (4)市 (5)ward_opt (6)addr_ext_opt
    # Pattern 2 groups: (7)pref (8)county (9)city_name (10)区|町|村 (11)addr_ext_opt
    # Pattern 3 groups: (12)county_opt (13)city_name (14)市 (15)ward_opt (16)addr_ext
    # Pattern 4 groups: (17)county_opt (18)city_name (19)区|町|村 (20)addr_ext
    detail_pattern = (
        f'({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(市)({city_name}区)?({addr_ext})?'
        f'|'
        f'({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(区|町|村)({addr_ext})?'
        f'|'
        f'{county_nopref_cap}({city_name_nopref})(市)({city_name_nopref}区)?({addr_ext})'
        f'|'
        f'{county_nopref_cap}({city_name_nopref})(区|町|村)({addr_ext})'
    )

    return basic_pattern, detail_pattern


_BASIC_PATTERN, _DETAIL_PATTERN = _build_patterns()


def extract_full_addresses(text: str) -> str:
    """
    Extract Japanese full addresses (including block/lot numbers) from plain text.

    Extracts addresses from prefecture down to 丁目・番地・号 or hyphenated form.
    Falls back to city/ward/town/village level when no street number is present.
    Returns results as a JSON array string.

    Args:
        text: Plain text to extract addresses from

    Returns:
        JSON string containing array of extracted full addresses

    Example:
        >>> text = "本社は東京都渋谷区道玄坂1丁目2番3号です。支社は大阪府大阪市北区梅田2-4-9。"
        >>> result = extract_full_addresses(text)
        >>> print(result)
        ["東京都渋谷区道玄坂1丁目2番3号", "大阪府大阪市北区梅田2-4-9"]
    """
    if not text:
        return json.dumps([], ensure_ascii=False)

    addresses = []
    seen = set()
    for match in re.finditer(_BASIC_PATTERN, text):
        address = match.group(0)
        if address not in seen:
            addresses.append(address)
            seen.add(address)

    return json.dumps(addresses, ensure_ascii=False, indent=2)


def extract_full_addresses_list(text: str) -> List[str]:
    """
    Extract Japanese full addresses from plain text.

    Returns results as a Python list.

    Args:
        text: Plain text to extract addresses from

    Returns:
        List of extracted full addresses
    """
    return json.loads(extract_full_addresses(text))


def extract_full_addresses_detailed(text: str) -> str:
    """
    Extract Japanese full addresses with detailed component breakdown.

    Returns addresses with structured components as a JSON array.

    Args:
        text: Plain text to extract addresses from

    Returns:
        JSON string containing array of address objects with components:
        - full_address: Complete address string
        - prefecture: Prefecture name (e.g., "東京都")
        - county: County name if present (e.g., "上北郡"), or null
        - city: City/ward/town/village (e.g., "渋谷区")
        - street_number: Street/block/lot info (e.g., "道玄坂1丁目2番3号"), or null
    """
    if not text:
        return json.dumps([], ensure_ascii=False)

    addresses = []
    seen = set()
    for match in re.finditer(_DETAIL_PATTERN, text):
        full_address = match.group(0)
        if full_address in seen:
            continue

        if match.group(1):       # Pattern 1: pref + 市
            prefecture = match.group(1)
            county = match.group(2)
            city = match.group(3) + match.group(4)  # name + 市
            if match.group(5):
                city += match.group(5)               # + ward (区)
            street_number = match.group(6)
        elif match.group(7):     # Pattern 2: pref + 区|町|村
            prefecture = match.group(7)
            county = match.group(8)
            city = match.group(9) + match.group(10)  # name + 区/町/村
            street_number = match.group(11)
        elif match.group(13):    # Pattern 3: no pref + 市
            prefecture = None
            county = match.group(12)
            city = match.group(13) + match.group(14)  # name + 市
            if match.group(15):
                city += match.group(15)                # + ward (区)
            street_number = match.group(16)
        else:                    # Pattern 4: no pref + 区|町|村
            prefecture = None
            county = match.group(17)
            city = match.group(18) + match.group(19)  # name + 区/町/村
            street_number = match.group(20)

        addresses.append({
            "full_address": full_address,
            "prefecture": prefecture,
            "county": county if county else None,
            "city": city,
            "street_number": street_number if street_number else None,
        })
        seen.add(full_address)

    return json.dumps(addresses, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    import io

    # Force UTF-8 encoding for stdin/stdout (Windows compatibility)
    if sys.platform == 'win32':
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text_content = f.read()
    else:
        text_content = sys.stdin.read()

    print(extract_full_addresses(text_content))
