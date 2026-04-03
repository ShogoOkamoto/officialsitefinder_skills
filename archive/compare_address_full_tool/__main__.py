"""
Command-line interface for compare_address_full_tool.

Usage:
    python -m compare_address_full_tool <address1> <address2> [-v] [-n]

Exit codes:
    0 — Addresses match (compatible)
    1 — Addresses do not match
"""

import sys
import argparse
import io
from . import compare_addresses, normalize_address, get_normalized_diff

# Force UTF-8 encoding for stdout/stderr (Windows compatibility)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description=(
            'Compare Japanese addresses ignoring zenkaku/hankaku, whitespace, '
            'kanji numerals, and 丁目/番地/号 vs hyphenated notation differences. '
            'Uses prefix/containment matching: an address with less detail '
            '(e.g. prefecture+city only) matches a more detailed one.'
        )
    )
    parser.add_argument('address1', help='First address to compare')
    parser.add_argument('address2', help='Second address to compare')
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed comparison with normalized forms and match type',
    )
    parser.add_argument(
        '-n', '--normalize',
        action='store_true',
        help='Only normalize and display the first address (ignores second address)',
    )

    args = parser.parse_args()

    # Normalize-only mode
    if args.normalize:
        normalized = normalize_address(args.address1)
        print(f"Original:   {args.address1}")
        print(f"Normalized: {normalized}")
        return 0

    # Verbose mode
    if args.verbose:
        result = get_normalized_diff(args.address1, args.address2)
        print("=" * 60)
        print("Address Comparison Result")
        print("=" * 60)
        print(f"Address 1 (original):   {result['address1_original']}")
        print(f"Address 1 (normalized): {result['address1_normalized']}")
        print()
        print(f"Address 2 (original):   {result['address2_original']}")
        print(f"Address 2 (normalized): {result['address2_normalized']}")
        print()
        match_label = 'EQUAL' if result['equal'] else 'NOT EQUAL'
        print(f"Addresses are {match_label}  [{result['match_type']}]")
        print("=" * 60)
        return 0 if result['equal'] else 1

    # Default mode
    is_equal = compare_addresses(args.address1, args.address2)
    print("EQUAL" if is_equal else "NOT EQUAL")
    return 0 if is_equal else 1


if __name__ == '__main__':
    sys.exit(main())
