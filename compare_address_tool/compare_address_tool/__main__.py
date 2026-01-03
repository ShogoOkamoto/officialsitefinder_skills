"""
Command-line interface for compare_address_tool.

This module allows the package to be run as a script using:
    python -m compare_address_tool
"""

import sys
import argparse
import io
from . import compare_addresses, normalize_address, get_normalized_diff

# Force UTF-8 encoding for stdout (Windows compatibility)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Compare Japanese addresses ignoring zenkaku/hankaku and whitespace differences'
    )

    parser.add_argument(
        'address1',
        help='First address to compare'
    )

    parser.add_argument(
        'address2',
        help='Second address to compare'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed comparison with normalized forms'
    )

    parser.add_argument(
        '-n', '--normalize',
        action='store_true',
        help='Only normalize and display the first address (ignores second address)'
    )

    args = parser.parse_args()

    # Normalize-only mode
    if args.normalize:
        normalized = normalize_address(args.address1)
        print(f"Original:   {args.address1}")
        print(f"Normalized: {normalized}")
        return 0

    # Compare mode
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
        print(f"Addresses are {'EQUAL' if result['equal'] else 'NOT EQUAL'}")
        print("=" * 60)
        return 0 if result['equal'] else 1
    else:
        is_equal = compare_addresses(args.address1, args.address2)
        if is_equal:
            print("EQUAL")
            return 0
        else:
            print("NOT EQUAL")
            return 1


if __name__ == '__main__':
    sys.exit(main())
