# compare-address-tool

A Python tool for comparing Japanese addresses while normalizing common variations such as full-width/half-width characters (zenkaku/hankaku) and whitespace differences.

## Project Overview

This is a pure Python library that provides address comparison functionality specifically designed for Japanese addresses. The tool normalizes various formatting differences to determine if two addresses are semantically equivalent, ignoring superficial differences like full-width vs. half-width characters and whitespace variations.

## Project Structure

```
compare_address_tool/
├── compare_address_tool/
│   ├── __init__.py          # Main library implementation
│   └── __main__.py          # CLI entry point for python -m
├── tests/
│   ├── __init__.py          # Test package initialization
│   └── test_compare_address.py  # Comprehensive test suite
├── pyproject.toml           # Project configuration and dependencies
├── README.md                # User documentation
├── CLAUDE.md                # Developer documentation (this file)
├── LICENSE                  # MIT License
└── .gitignore              # Git ignore rules
```

## Key Files

### compare_address_tool/__init__.py

Main library implementation containing:
- `normalize_address(address: str) -> str`: Normalizes a single address
- `compare_addresses(address1: str, address2: str) -> bool`: Compares two addresses for equivalence
- `get_normalized_diff(address1: str, address2: str) -> dict`: Returns detailed comparison results

**Normalization Process:**
1. Remove all whitespace (spaces, tabs, newlines, full-width spaces)
2. Convert full-width (zenkaku) characters to half-width (hankaku) using Unicode NFKC normalization
3. Convert to lowercase for case-insensitive comparison

### compare_address_tool/__main__.py

CLI entry point that allows running the tool with `python -m compare_address_tool`. Provides:
- Basic comparison mode (default)
- Verbose mode (`-v`/`--verbose`) for detailed output
- Normalize-only mode (`-n`/`--normalize`) to see normalization of a single address

## Development Setup

### Prerequisites

- Python 3.8 or higher
- No external dependencies required (uses only Python standard library)

### Installation

Install in development mode:
```bash
pip install -e .
```

Install with development dependencies (for testing):
```bash
pip install -e ".[dev]"
```

### No Environment Variables Required

Unlike the google-search-mcp project, this tool does not require any API keys or environment variables. It's a pure computational library with no external service dependencies.

## Dependencies

**Core Dependencies:** None! The library uses only Python's standard library:
- `unicodedata`: For Unicode normalization (NFKC)

**Development Dependencies** (optional, for testing):
- `pytest>=7.0.0`: Testing framework
- `pytest-cov>=4.0.0`: Coverage reporting

## Architecture

### Core Functions

**Function: normalize_address**
- **Purpose**: Normalizes a single address string by removing whitespace and converting zenkaku to hankaku
- **Input**: `address` (str) - The address to normalize
- **Output**: Normalized address string
- **Algorithm**:
  1. Remove all whitespace using `''.join(address.split())`
  2. Apply NFKC normalization to convert compatible characters
  3. Convert to lowercase

**Function: compare_addresses**
- **Purpose**: Compares two addresses for equivalence
- **Input**: `address1` (str), `address2` (str)
- **Output**: Boolean indicating equivalence
- **Algorithm**: Normalize both addresses and compare for string equality

**Function: get_normalized_diff**
- **Purpose**: Provides detailed comparison information
- **Input**: `address1` (str), `address2` (str)
- **Output**: Dictionary with original and normalized forms, plus equality flag

### Unicode Normalization Details

The tool uses Unicode NFKC (Compatibility Decomposition, followed by Canonical Composition) normalization:

- **Full-width → Half-width**: `１２３` → `123`, `ＡＢＣ` → `abc`
- **Katakana**: Full-width katakana may be converted to half-width
- **Symbols**: `−` (U+2212) → `-` (U+002D)
- **Parentheses**: `（）` → `()`

NFKC was chosen because:
1. It handles the most common zenkaku/hankaku variations in Japanese text
2. It's part of Python's standard library (no dependencies)
3. It's fast and well-tested
4. It preserves kanji characters while normalizing alphanumerics

## Code Guidelines

### Error Handling

The code includes error handling for:
- **Type validation**: Raises `TypeError` if non-string arguments are passed
- **Input validation**: All string inputs are accepted (no format requirements)

### Design Principles

1. **Pure functions**: All functions are pure (no side effects)
2. **Immutability**: Original input strings are never modified
3. **Type safety**: Explicit type hints for all function signatures
4. **Simplicity**: Minimal code, no external dependencies
5. **Unicode-aware**: Proper handling of multi-byte characters

### Performance Considerations

- `normalize_address()` has O(n) time complexity where n is the length of the input
- `compare_addresses()` is O(n + m) where n and m are the lengths of the two inputs
- Normalization is fast enough for real-time use (< 1ms for typical addresses)
- No caching is implemented to keep the library simple and stateless

## Testing

### Running Tests

Install the package with development dependencies:
```bash
pip install -e ".[dev]"
```

Run all tests:
```bash
pytest
```

Run tests with verbose output:
```bash
pytest -v
```

Run tests with coverage report:
```bash
pytest --cov=compare_address_tool --cov-report=html
```

Run specific test class:
```bash
pytest tests/test_compare_address.py::TestNormalizeAddress
```

### Test Structure

The test suite (tests/test_compare_address.py) is organized into test classes:

**TestNormalizeAddress:**
- Whitespace removal (spaces, tabs, newlines, full-width spaces)
- Zenkaku to hankaku conversion (numbers, alphanumerics, katakana)
- Case conversion
- Edge cases (empty strings, whitespace-only strings)
- Type validation

**TestCompareAddresses:**
- Identical addresses
- Addresses differing only in whitespace
- Addresses differing only in zenkaku/hankaku
- Different addresses (should not match)
- Complex real-world addresses
- Type validation

**TestGetNormalizedDiff:**
- Equal addresses
- Different addresses
- Preservation of original addresses
- Result structure validation

**TestEdgeCases:**
- Unicode normalization edge cases
- Very long addresses
- Special characters
- Mixed Japanese/English
- Parentheses and brackets

### Test Coverage

The test suite aims for 100% code coverage. Key areas:
- All functions are tested
- All error paths are tested
- Edge cases are comprehensively covered
- Real-world use cases are included

### Writing New Tests

When adding new functionality:

1. Add tests to the appropriate test class or create a new class
2. Follow the naming convention: `test_<description>`
3. Use descriptive test names that explain what is being tested
4. Include docstrings explaining the test purpose
5. Test both success and failure cases
6. Use pytest assertions (`assert`, `pytest.raises`)

Example test structure:
```python
def test_new_feature(self):
    """Test that new feature works correctly."""
    # Arrange
    input_data = "test input"
    expected_output = "expected"

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

## Manual Testing

### Testing the Library

```python
from compare_address_tool import compare_addresses, normalize_address

# Test normalization
print(normalize_address("東京都　渋谷区　１−２−３"))
# Output: 東京都渋谷区1-2-3

# Test comparison
print(compare_addresses("東京都　渋谷区", "東京都渋谷区"))
# Output: True
```

### Testing the CLI

```bash
# Basic comparison
python -m compare_address_tool "東京都　渋谷区" "東京都渋谷区"

# Verbose comparison
python -m compare_address_tool -v "東京都　渋谷区　１−２−３" "東京都渋谷区1-2-3"

# Normalize only
python -m compare_address_tool -n "東京都　渋谷区　１−２−３" dummy
```

### Testing After Installation

If installed as a package:
```bash
compare-address "東京都　渋谷区" "東京都渋谷区"
```

## Common Issues and Solutions

### Unicode Normalization Edge Cases

**Issue:** Some Unicode characters may not normalize as expected.

**Example:** Circled numbers (①②③) may or may not be normalized depending on the Unicode version.

**Solution:** The tool uses NFKC which is standardized, but be aware that some edge cases exist. If you need custom normalization, extend the `normalize_address` function.

### Japanese Character Variants

**Issue:** Some kanji have multiple Unicode representations (e.g., 吉 has variants).

**Current Behavior:** NFKC normalization handles some variants but not all.

**Solution:** For production use with high-accuracy requirements, consider adding additional normalization layers or using a specialized Japanese text normalization library.

### Performance with Very Long Addresses

**Issue:** Very long addresses (thousands of characters) may be slow.

**Current Performance:** O(n) time complexity is efficient for normal addresses (< 200 characters).

**Solution:** For bulk processing, consider batching or parallel processing of addresses.

## Making Changes

### Adding New Normalization Rules

To add custom normalization beyond NFKC:

1. Modify the `normalize_address` function in `compare_address_tool/__init__.py`
2. Add the transformation before or after NFKC normalization
3. Add comprehensive tests for the new rule
4. Update documentation

Example:
```python
def normalize_address(address: str) -> str:
    # Existing code...
    normalized = unicodedata.normalize('NFKC', normalized)

    # Add custom normalization
    normalized = normalized.replace('番地', '')  # Remove 番地

    normalized = normalized.lower()
    return normalized
```

### Adding New Functions

To add new functions to the library:

1. Add the function to `compare_address_tool/__init__.py`
2. Include proper docstring with Args, Returns, and Examples
3. Add the function to `__all__` list
4. Add comprehensive tests
5. Update README.md with usage examples

### Modifying CLI Behavior

The CLI is in `compare_address_tool/__main__.py`. When modifying:

1. Update the argument parser if adding new options
2. Maintain backward compatibility with existing flags
3. Add tests for new CLI functionality (use subprocess)
4. Update README.md with new CLI examples

### Updating Dependencies

This package intentionally has no runtime dependencies. If you must add a dependency:

1. Update `dependencies` list in `pyproject.toml`
2. Document why the dependency is necessary
3. Consider if it can be made optional
4. Update `requires-python` if needed
5. Test with multiple Python versions

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md (if exists) or README.md with changes
3. Run full test suite: `pytest`
4. Build the package: `python -m build`
5. Test the built package locally
6. Create a git tag: `git tag v0.1.0`
7. Push tag: `git push origin v0.1.0`
8. Publish to PyPI: `python -m twine upload dist/*`

## Best Practices

### When Using This Library

- **Validate input**: Always validate that inputs are strings before calling functions
- **Handle edge cases**: Consider empty strings, very long addresses, unusual characters
- **Test with real data**: Use actual Japanese addresses from your dataset for testing
- **Document assumptions**: If your use case has specific requirements, document them

### When Contributing

- **Keep it simple**: This library is intentionally minimal and dependency-free
- **Write tests first**: Use TDD (Test-Driven Development) approach
- **Add docstrings**: All public functions must have comprehensive docstrings
- **Maintain compatibility**: Don't break existing APIs without major version bump
- **Consider performance**: Profile before optimizing, but avoid unnecessary complexity

### Code Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Write descriptive variable names
- Keep functions focused and single-purpose
- Prefer clarity over cleverness

## Advanced Topics

### Unicode Normalization Forms

Python's `unicodedata` module supports four normalization forms:

- **NFC**: Canonical Decomposition, followed by Canonical Composition
- **NFD**: Canonical Decomposition
- **NFKC**: Compatibility Decomposition, followed by Canonical Composition (used by this tool)
- **NFKD**: Compatibility Decomposition

We use NFKC because:
- It converts compatible characters to canonical forms (zenkaku → hankaku)
- It composes characters (combining marks are combined)
- It's appropriate for string comparison

### Alternative Approaches

Other approaches considered but not implemented:

1. **Regular expressions for zenkaku/hankaku**: More explicit but requires maintaining mapping tables
2. **Japanese text processing libraries**: Would add dependencies
3. **Custom normalization tables**: More control but harder to maintain
4. **Machine learning**: Overkill for this deterministic problem

The current approach balances simplicity, performance, and correctness.

### Integration Examples

**With Django models:**
```python
from django.db import models
from compare_address_tool import normalize_address

class Address(models.Model):
    original = models.CharField(max_length=255)
    normalized = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        self.normalized = normalize_address(self.original)
        super().save(*args, **kwargs)
```

**With Pandas:**
```python
import pandas as pd
from compare_address_tool import normalize_address

df['normalized_address'] = df['address'].apply(normalize_address)
```

**For deduplication:**
```python
from compare_address_tool import normalize_address

def deduplicate_addresses(addresses):
    seen = set()
    unique = []
    for addr in addresses:
        normalized = normalize_address(addr)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(addr)
    return unique
```

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'compare_address_tool'`

**Solution:**
1. Ensure the package is installed: `pip install -e .`
2. Check you're in the correct virtual environment
3. Verify installation: `pip show compare-address-tool`

### Test Failures

**Problem:** Tests fail after making changes

**Solution:**
1. Read the test failure message carefully
2. Check if you broke backward compatibility
3. Update tests if behavior intentionally changed
4. Run single test to isolate: `pytest tests/test_compare_address.py::TestClass::test_method`

### CLI Not Working

**Problem:** `compare-address` command not found

**Solution:**
1. Ensure package is installed: `pip install -e .`
2. Use full path to Python if needed
3. Alternative: Use `python -m compare_address_tool` instead

## Future Enhancements

Potential features for future versions:

1. **Address component extraction**: Parse addresses into structured components (prefecture, city, ward, etc.)
2. **Fuzzy matching**: Allow similarity scoring instead of exact match
3. **Abbreviation handling**: Normalize common abbreviations (都 ↔ 東京都)
4. **Building/apartment handling**: Special handling for building names and unit numbers
5. **Configuration options**: Allow users to customize normalization rules
6. **Batch processing**: Optimized functions for processing many addresses at once
7. **Address validation**: Check if an address is valid/exists

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## See Also

- [README.md](README.md) - User documentation and quick start guide
- [Python unicodedata documentation](https://docs.python.org/3/library/unicodedata.html)
- [Unicode NFKC Normalization](https://unicode.org/reports/tr15/)
