"""Japanese address extraction tool.

This module provides functionality to extract Japanese addresses
from plain text and return them in JSON format.
"""

from .extract import extract_addresses, extract_addresses_list, extract_addresses_detailed

__all__ = ['extract_addresses', 'extract_addresses_list', 'extract_addresses_detailed']
