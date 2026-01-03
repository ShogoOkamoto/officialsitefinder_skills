"""Japanese address extraction module.

This module extracts Japanese addresses (from prefecture to city/ward/town/village)
from plain text and returns them as a JSON array.
"""

import re
import json
from typing import List, Dict


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


def extract_addresses(text: str) -> str:
    """
    Extract Japanese addresses from plain text.

    Extracts addresses from prefecture to city/ward/town/village level.
    Returns results as a JSON array string.

    Args:
        text: Plain text to extract addresses from

    Returns:
        JSON string containing array of extracted addresses

    Example:
        >>> text = "本社は東京都渋谷区にあります。支社は大阪府大阪市です。"
        >>> result = extract_addresses(text)
        >>> print(result)
        ["東京都渋谷区", "大阪府大阪市"]
    """
    if not text:
        return json.dumps([], ensure_ascii=False)

    addresses = []

    # Create regex pattern for prefectures
    prefecture_pattern = '|'.join(re.escape(pref) for pref in PREFECTURES)

    # Pattern to match: Prefecture + (optional: gun/county) + city/ward/town/village
    # Examples: 東京都渋谷区, 北海道札幌市, 京都府京都市中京区, 神奈川県横浜市青葉区
    # Pattern explanation:
    # - (prefecture): One of 47 prefectures
    # - ([^と、。\s]*郡)?: Optional county (郡) - excludes separators
    # - City/ward/town/village name: Uses negative lookahead to exclude delimiters
    # - (市|区|町|村): City, ward, town, or village suffix
    # - Additional ward after city (limited to reasonable length)

    # Pattern for city/ward/town/village names - excludes common delimiters
    city_name = r'(?:(?!と|や|及び|、|。)[ぁ-んァ-ヶー一-龠々\d])+'

    pattern = f'({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(市)({city_name}区)?|({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(区|町|村)'

    # Find all matches
    matches = re.finditer(pattern, text)

    seen = set()  # To avoid duplicates
    for match in matches:
        address = match.group(0)
        # Only add if not already seen (avoid duplicates)
        if address not in seen:
            addresses.append(address)
            seen.add(address)

    # Return as JSON array
    return json.dumps(addresses, ensure_ascii=False, indent=2)


def extract_addresses_list(text: str) -> List[str]:
    """
    Extract Japanese addresses from plain text.

    Extracts addresses from prefecture to city/ward/town/village level.
    Returns results as a Python list.

    Args:
        text: Plain text to extract addresses from

    Returns:
        List of extracted addresses
    """
    json_result = extract_addresses(text)
    return json.loads(json_result)


def extract_addresses_detailed(text: str) -> str:
    """
    Extract Japanese addresses with detailed information.

    Returns addresses with structured components (prefecture, city, etc.)
    as a JSON array.

    Args:
        text: Plain text to extract addresses from

    Returns:
        JSON string containing array of address objects with components
    """
    if not text:
        return json.dumps([], ensure_ascii=False)

    addresses = []

    # Create regex pattern for prefectures
    prefecture_pattern = '|'.join(re.escape(pref) for pref in PREFECTURES)

    # Pattern for city/ward/town/village names - excludes common delimiters
    city_name = r'(?:(?!と|や|及び|、|。)[ぁ-んァ-ヶー一-龠々\d])+'

    # Pattern with capture groups for each component
    pattern = f'({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(市)({city_name}区)?|({prefecture_pattern})([^と、。\\s]*郡)?({city_name})(区|町|村)'

    matches = re.finditer(pattern, text)

    seen = set()
    for match in matches:
        full_address = match.group(0)

        if full_address not in seen:
            # Check which pattern matched (city pattern or ward/town/village pattern)
            if match.group(1):  # First pattern: prefecture + city (+ optional ward)
                prefecture = match.group(1)
                county = match.group(2)
                city_name = match.group(3) + match.group(4)  # name + 市
                if match.group(5):  # Additional ward
                    city_name += match.group(5)
            else:  # Second pattern: prefecture + ward/town/village
                prefecture = match.group(6)
                county = match.group(7)
                city_name = match.group(8) + match.group(9)  # name + 区/町/村

            address_obj = {
                "full_address": full_address,
                "prefecture": prefecture,
                "county": county if county else None,
                "city": city_name
            }
            addresses.append(address_obj)
            seen.add(full_address)

    return json.dumps(addresses, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys
    import io

    # Force UTF-8 encoding for stdin/stdout (Windows compatibility)
    if sys.platform == 'win32':
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Read text from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            text_content = f.read()
    else:
        text_content = sys.stdin.read()

    # Extract addresses and print JSON
    result = extract_addresses(text_content)
    print(result)
