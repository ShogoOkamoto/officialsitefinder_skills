# compare-address-tool

A Python tool for comparing Japanese addresses while normalizing common variations such as full-width/half-width characters (zenkaku/hankaku) and whitespace differences.

## Features

- **Zenkaku/Hankaku Normalization**: Automatically converts full-width characters to half-width (e.g., `１２３` → `123`, `ＡＢＣ` → `ABC`)
- **Whitespace Handling**: Ignores all types of whitespace (spaces, tabs, newlines, full-width spaces)
- **Case Insensitive**: Treats uppercase and lowercase as equivalent
- **Simple API**: Easy-to-use functions for address comparison and normalization
- **CLI Support**: Command-line interface for quick comparisons
- **Pure Python**: No external dependencies required

## Installation

Install from PyPI:

```bash
pip install compare-address-tool
```

Or install from source:

```bash
git clone https://github.com/yourusername/compare-address-tool.git
cd compare-address-tool
pip install -e .
```

## Usage

### Python API

```python
from compare_address_tool import compare_addresses, normalize_address, get_normalized_diff

# Compare two addresses
address1 = "東京都　渋谷区　恵比寿南　１−２−３"
address2 = "東京都渋谷区恵比寿南1-2-3"

# Simple comparison
is_equal = compare_addresses(address1, address2)
print(is_equal)  # True

# Normalize a single address
normalized = normalize_address("東京都　渋谷区　１−２−３")
print(normalized)  # "東京都渋谷区1-2-3"

# Get detailed comparison
result = get_normalized_diff(address1, address2)
print(result['equal'])  # True
print(result['address1_normalized'])  # "東京都渋谷区恵比寿南1-2-3"
print(result['address2_normalized'])  # "東京都渋谷区恵比寿南1-2-3"
```

### Command Line Interface

Compare two addresses:

```bash
compare-address "東京都　渋谷区　１−２−３" "東京都渋谷区1-2-3"
# Output: EQUAL

compare-address "東京都渋谷区" "大阪府大阪市"
# Output: NOT EQUAL
```

Verbose mode (show normalized forms):

```bash
compare-address -v "東京都　渋谷区　１−２−３" "東京都渋谷区1-2-3"
# Output:
# ============================================================
# Address Comparison Result
# ============================================================
# Address 1 (original):   東京都　渋谷区　１−２−３
# Address 1 (normalized): 東京都渋谷区1-2-3
#
# Address 2 (original):   東京都渋谷区1-2-3
# Address 2 (normalized): 東京都渋谷区1-2-3
#
# Addresses are EQUAL
# ============================================================
```

Normalize only (show normalized form of a single address):

```bash
compare-address -n "東京都　渋谷区　１−２−３" dummy
# Output:
# Original:   東京都　渋谷区　１−２−３
# Normalized: 東京都渋谷区1-2-3
```

You can also run as a Python module:

```bash
python -m compare_address_tool "東京都　渋谷区" "東京都渋谷区"
```

## What Gets Normalized?

The tool normalizes the following differences:

1. **Full-width to Half-width**:
   - Numbers: `１２３` → `123`
   - Latin letters: `ＡＢＣ` → `abc`
   - Symbols: `−` → `-`
   - Parentheses: `（）` → `()`

2. **Whitespace**:
   - Spaces (half-width and full-width): ` ` and `　`
   - Tabs: `\t`
   - Newlines: `\n`
   - Other Unicode whitespace characters

3. **Case**:
   - Uppercase to lowercase: `ABC` → `abc`

## Examples

```python
from compare_address_tool import compare_addresses

# Different spacing - EQUAL
compare_addresses("東京都渋谷区", "東京都　渋谷区")  # True

# Zenkaku vs Hankaku numbers - EQUAL
compare_addresses("東京都渋谷区１−２−３", "東京都渋谷区1-2-3")  # True

# Mixed variations - EQUAL
compare_addresses(
    "東京都　渋谷区　恵比寿南　１−２−３　恵比寿ビル　５Ｆ",
    "東京都渋谷区恵比寿南1-2-3恵比寿ビル5F"
)  # True

# Actually different addresses - NOT EQUAL
compare_addresses("東京都渋谷区", "大阪府大阪市")  # False
```

## API Reference

### `compare_addresses(address1: str, address2: str) -> bool`

Compare two addresses for equivalence after normalization.

**Parameters:**
- `address1` (str): First address to compare
- `address2` (str): Second address to compare

**Returns:**
- `bool`: True if addresses are equivalent, False otherwise

**Raises:**
- `TypeError`: If either argument is not a string

### `normalize_address(address: str) -> str`

Normalize an address string.

**Parameters:**
- `address` (str): Address string to normalize

**Returns:**
- `str`: Normalized address

**Raises:**
- `TypeError`: If address is not a string

### `get_normalized_diff(address1: str, address2: str) -> dict`

Get detailed comparison information.

**Parameters:**
- `address1` (str): First address to compare
- `address2` (str): Second address to compare

**Returns:**
- `dict`: Dictionary with keys:
  - `equal` (bool): Whether addresses are equivalent
  - `address1_original` (str): Original first address
  - `address2_original` (str): Original second address
  - `address1_normalized` (str): Normalized first address
  - `address2_normalized` (str): Normalized second address

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/compare-address-tool.git
cd compare-address-tool

# Install in development mode with test dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=compare_address_tool --cov-report=html

# Run specific test file
pytest tests/test_compare_address.py

# Run with verbose output
pytest -v
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## See Also

- [Developer Documentation](CLAUDE.md) - Comprehensive documentation for developers
