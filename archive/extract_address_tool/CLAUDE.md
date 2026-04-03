# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python module for extracting Japanese addresses from plain text. It identifies and extracts addresses from prefecture to city/ward/town/village level, returning them as structured JSON data. The module is designed to be used as a standalone tool or integrated into other projects as part of the larger officialsitefinder_skills suite.

## Testing

Run all tests:
```bash
pytest test_extract.py -v
```

Run tests from the module directly:
```bash
python test_extract.py
```

Run a single test:
```bash
pytest test_extract.py::TestExtractAddresses::test_single_address -v
```

## Running the Module

### As a Python module:
```bash
# From stdin
python -m extract_address_tool.extract

# From file
python -m extract_address_tool.extract input.txt

# Direct invocation
python extract.py < input.txt
```

### Programmatic usage:
```python
from extract_address_tool.extract import extract_addresses, extract_addresses_list, extract_addresses_detailed

# Returns JSON string
json_result = extract_addresses(text)

# Returns Python list
addresses = extract_addresses_list(text)

# Returns JSON with detailed components (prefecture, county, city)
detailed_result = extract_addresses_detailed(text)
```

## Architecture

### Core Components

**extract.py** - Main extraction logic
- `PREFECTURES`: List of all 47 Japanese prefectures
- `extract_addresses()`: Main extraction function returning JSON string
- `extract_addresses_list()`: Wrapper returning Python list
- `extract_addresses_detailed()`: Returns structured JSON with address components (full_address, prefecture, county, city)

**Regex Pattern Strategy**:
The module uses a complex regex pattern that handles two main cases:
1. Prefecture + (optional county) + city name + 市 + (optional ward)
2. Prefecture + (optional county) + name + (区|町|村)

The pattern excludes common Japanese delimiters (と, や, 及び, 、, 。) to properly separate multiple addresses in text.

**Duplicate Handling**:
Uses a `seen` set to track and eliminate duplicate addresses within the same text.

### Test Structure

**test_extract.py** - Comprehensive test suite
- `TestExtractAddresses`: Tests for the main `extract_addresses()` function
  - Single/multiple addresses
  - All prefecture types (都/道/府/県)
  - Administrative divisions (市/区/町/村)
  - Counties (郡)
  - Complex formats (city + ward)
  - Edge cases (empty input, duplicates, no addresses)
- `TestExtractAddressesList`: Tests for list output format
- `TestExtractAddressesDetailed`: Tests for detailed structured output

### Supported Address Formats

- **Prefecture types**: 都 (Tokyo), 道 (Hokkaido), 府 (Kyoto/Osaka), 県 (all other prefectures)
- **Administrative divisions**: 市 (cities), 区 (wards), 町 (towns), 村 (villages), 郡 (counties)
- **Complex formats**:
  - City + Ward: 横浜市青葉区, 京都市中京区
  - Prefecture + County + Town: 青森県上北郡六戸町
  - Prefecture + Ward: 東京都渋谷区

### Limitations

- Only extracts down to city/ward/town/village level (no street addresses or building names)
- Requires prefecture name to be present in the text
- Does not infer prefecture from city name alone
- Text must contain valid Japanese address format patterns

## Integration Context

This module is part of the larger **officialsitefinder_skills** project, which includes:
- **extract_address_tool** (this module): Extract Japanese addresses from text
- **google_search_tool**: Perform Google searches via CLI
- **playwright_download_tool**: Download web page HTML content
- **google_search_skill** and **extract_address_skill**: Claude Code skills that use these tools

The intended workflow (described in officialsitefinder_skills.md) uses this module to:
1. Extract prefecture/city from facility addresses
2. Use those addresses to validate search results from Google
3. Match addresses found in downloaded web pages against the original facility address

## Development Notes

### Adding New Prefecture Support
The `PREFECTURES` list in extract.py:13-22 contains all 47 Japanese prefectures. This should only need updating if administrative boundaries change (extremely rare).

### Modifying Regex Pattern
The regex pattern in extract.py:64 is complex. When modifying:
- Test against debug_test.py to see how patterns match
- Ensure delimiter exclusion (と, や, 及び, 、, 。) works correctly
- Update tests to cover new cases
- Run full test suite to prevent regressions

### Working with debug_test.py
This file provides a simple debugging environment to test regex patterns:
```bash
python debug_test.py
```
It prints detailed match information including groups and positions.
