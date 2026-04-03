"""Japanese address extraction module.

This module extracts Japanese addresses (from prefecture to city/ward/town/village)
from plain text and returns them as JSON. Street-level details (丁目・番地・号) are
intentionally omitted; use extract_full_address_tool if those are needed.
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
    """Build regex patterns for city-level address extraction."""
    prefecture_pattern = '|'.join(re.escape(pref) for pref in PREFECTURES)

    # City/ward/town/village name - excludes common delimiters
    city_name = r'(?:(?!と|や|及び|、|。)[ぁ-んァ-ヶー一-龠々\d])+'

    # Non-capturing pattern for basic extraction:
    #   Pattern 1: 東京都 → 大阪市 → (北区)?
    #   Pattern 2: 青森県上北郡 → 六戸町
    basic_pattern = (
        f'(?:{prefecture_pattern})(?:[^と、。\\s]*郡)?(?:{city_name})市(?:{city_name}区)?'
        f'|'
        f'(?:{prefecture_pattern})(?:[^と、。\\s]*郡)?(?:{city_name})(?:区|町|村)'
    )

    # Capturing pattern for detailed extraction
    # Pattern 1 groups: (1)pref (2)county? (3)city_name (4)市 (5)ward_opt?
    # Pattern 2 groups: (6)pref (7)county? (8)city_name (9)区|町|村
    detail_pattern = (
        f'({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(市)({city_name}区)?'
        f'|'
        f'({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(区|町|村)'
    )

    return basic_pattern, detail_pattern


_BASIC_PATTERN, _DETAIL_PATTERN = _build_patterns()


def extract_addresses(text: str) -> str:
    """
    Extract Japanese addresses from plain text (up to city/ward/town/village level).

    Street-level details (丁目・番地・号, hyphenated block numbers) are NOT included.
    Returns results as a JSON array string.

    Args:
        text: Plain text to extract addresses from

    Returns:
        JSON string containing array of extracted addresses

    Example:
        >>> text = "本社は東京都渋谷区道玄坂1丁目2番3号です。支社は大阪府大阪市です。"
        >>> result = extract_addresses(text)
        >>> print(result)
        ["東京都渋谷区", "大阪府大阪市"]
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


def extract_addresses_list(text: str) -> List[str]:
    """
    Extract Japanese addresses from plain text (up to city/ward/town/village level).

    Returns results as a Python list.

    Args:
        text: Plain text to extract addresses from

    Returns:
        List of extracted addresses
    """
    return json.loads(extract_addresses(text))


def extract_addresses_detailed(text: str) -> str:
    """
    Extract Japanese addresses with detailed component breakdown.

    Returns addresses with structured components (prefecture, county, city)
    as a JSON array. Street-level details are NOT included.

    Args:
        text: Plain text to extract addresses from

    Returns:
        JSON string containing array of address objects with components:
        - full_address: Complete address string (city level)
        - prefecture: Prefecture name (e.g., "東京都")
        - county: County name if present (e.g., "上北郡"), or null
        - city: City/ward/town/village (e.g., "渋谷区")
    """
    if not text:
        return json.dumps([], ensure_ascii=False)

    addresses = []
    seen = set()
    for match in re.finditer(_DETAIL_PATTERN, text):
        full_address = match.group(0)
        if full_address in seen:
            continue

        if match.group(1):  # Pattern 1: city (市) form
            prefecture = match.group(1)
            county = match.group(2)
            city = match.group(3) + match.group(4)  # name + 市
            if match.group(5):
                city += match.group(5)               # + ward (区)
        else:               # Pattern 2: ward/town/village (区|町|村) form
            prefecture = match.group(6)
            county = match.group(7)
            city = match.group(8) + match.group(9)  # name + 区/町/村

        addresses.append({
            "full_address": full_address,
            "prefecture": prefecture,
            "county": county if county else None,
            "city": city,
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

    print(extract_addresses(text_content))
