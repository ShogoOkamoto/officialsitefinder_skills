"""
compare_address_tool - Japanese Address Comparison Tool

This module provides functionality to compare Japanese addresses while normalizing
common variations such as full-width/half-width characters and whitespace.
"""

import unicodedata


def normalize_address(address: str) -> str:
    """
    Normalize a Japanese address for comparison.

    Normalization includes:
    - Converting full-width (zenkaku) characters to half-width (hankaku)
    - Removing all whitespace (spaces, tabs, newlines, etc.)
    - Converting to lowercase for case-insensitive comparison

    Args:
        address: The address string to normalize

    Returns:
        Normalized address string

    Examples:
        >>> normalize_address("東京都　渋谷区")
        '東京都渋谷区'
        >>> normalize_address("１２３")
        '123'
    """
    if not isinstance(address, str):
        raise TypeError(f"Address must be a string, got {type(address).__name__}")

    # Remove all whitespace characters (spaces, tabs, newlines, etc.)
    normalized = ''.join(address.split())

    # Convert full-width (zenkaku) characters to half-width (hankaku)
    # NFKC normalization converts compatible characters to their canonical form
    # This handles full-width alphanumerics, katakana, and symbols
    normalized = unicodedata.normalize('NFKC', normalized)

    # NFKC doesn't normalize certain characters, so handle them explicitly
    # Replace minus sign (U+2212) with hyphen-minus (U+002D)
    normalized = normalized.replace('\u2212', '-')

    # Convert to lowercase for case-insensitive comparison
    normalized = normalized.lower()

    return normalized


def compare_addresses(address1: str, address2: str) -> bool:
    """
    Compare two Japanese addresses for equivalence.

    The comparison normalizes both addresses to ignore:
    - Full-width (zenkaku) vs half-width (hankaku) character differences
    - Whitespace differences (spaces, tabs, newlines)
    - Case differences

    Args:
        address1: First address to compare
        address2: Second address to compare

    Returns:
        True if the addresses are equivalent after normalization, False otherwise

    Examples:
        >>> compare_addresses("東京都　渋谷区", "東京都渋谷区")
        True
        >>> compare_addresses("東京都１−２−３", "東京都1-2-3")
        True
        >>> compare_addresses("東京都渋谷区", "大阪府大阪市")
        False
    """
    if not isinstance(address1, str):
        raise TypeError(f"address1 must be a string, got {type(address1).__name__}")
    if not isinstance(address2, str):
        raise TypeError(f"address2 must be a string, got {type(address2).__name__}")

    normalized1 = normalize_address(address1)
    normalized2 = normalize_address(address2)

    return normalized1 == normalized2


def get_normalized_diff(address1: str, address2: str) -> dict:
    """
    Get detailed comparison information between two addresses.

    Args:
        address1: First address to compare
        address2: Second address to compare

    Returns:
        Dictionary containing:
        - 'equal': bool indicating if addresses are equivalent
        - 'address1_original': Original first address
        - 'address2_original': Original second address
        - 'address1_normalized': Normalized first address
        - 'address2_normalized': Normalized second address

    Examples:
        >>> result = get_normalized_diff("東京都　１−２", "東京都1-2")
        >>> result['equal']
        True
        >>> result['address1_normalized']
        '東京都1-2'
    """
    normalized1 = normalize_address(address1)
    normalized2 = normalize_address(address2)

    return {
        'equal': normalized1 == normalized2,
        'address1_original': address1,
        'address2_original': address2,
        'address1_normalized': normalized1,
        'address2_normalized': normalized2
    }


__all__ = ['normalize_address', 'compare_addresses', 'get_normalized_diff']
