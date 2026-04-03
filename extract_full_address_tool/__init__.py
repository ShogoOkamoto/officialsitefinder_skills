"""Japanese full address extraction tool.

This module provides functionality to extract Japanese full addresses
(including 丁目・番地・号 and hyphenated forms) from plain text.
"""

from .extract import (
    extract_full_addresses,
    extract_full_addresses_list,
    extract_full_addresses_detailed,
)

__all__ = [
    'extract_full_addresses',
    'extract_full_addresses_list',
    'extract_full_addresses_detailed',
]
