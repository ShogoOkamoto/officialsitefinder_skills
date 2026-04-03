---
name: extract-address-skill
description: Extract Japanese addresses (from prefecture to city/ward/town/village) from plain text. Use when users need to find and extract structured address information from documents, emails, or any text containing Japanese addresses.
allowed-tools: Bash(python:*)
---

# Extract Address Skill

## Overview

This Skill enables Claude to extract Japanese addresses from plain text using the `extract_address_tool` module. It identifies and extracts addresses from prefecture to city/ward/town/village level, returning them as structured JSON data.

## When to Use This Skill

Use this Skill when:
- Users need to extract addresses from documents, emails, or web content
- Processing text that contains multiple Japanese addresses
- Converting unstructured text into structured address data
- Validating or identifying addresses in large text files
- Building address databases from text sources
- Users explicitly request address extraction

## Instructions

When extracting addresses from text, follow these steps:

### 1. Receive or Prepare the Text

- Get the text from the user directly
- Or read from a file if the user provides a file path
- Ensure the text is in plain text format (not binary)

### 2. Execute the Address Extraction

Run the extraction using the extract_address_tool module:

```bash
python -c "from extract_address_tool.extract import extract_addresses; print(extract_addresses('your text here'))"
```

**For file input:**
```bash
python -m extract_address_tool.extract < input.txt
```

Or:
```bash
python -m extract_address_tool.extract input.txt
```

**For direct text input:**
```bash
python -c "from extract_address_tool.extract import extract_addresses; import sys; text = '''本社は東京都渋谷区にあります。支社は大阪府大阪市です。'''; print(extract_addresses(text))"
```

### 3. Parse and Present Results

After receiving the extraction results:

1. **Parse the JSON**: The output is a JSON array of extracted addresses
2. **Check for empty results**: If no addresses found, inform the user
3. **Present clearly**: Display addresses in a readable format
4. **Provide context**: Explain what was found and any patterns noticed

**Presentation format:**

```
I found [N] address(es) in the text:

1. [Address 1]
2. [Address 2]
...

[Additional observations or recommendations]
```

### 4. Alternative Output Formats

**Standard output (JSON array):**
```python
from extract_address_tool.extract import extract_addresses
result = extract_addresses(text)  # Returns JSON string
```

**Python list:**
```python
from extract_address_tool.extract import extract_addresses_list
addresses = extract_addresses_list(text)  # Returns Python list
```

**Detailed structure:**
```python
from extract_address_tool.extract import extract_addresses_detailed
result = extract_addresses_detailed(text)  # Returns JSON with components
```

The detailed format includes:
- `full_address`: Complete address string
- `prefecture`: Prefecture name (e.g., "東京都")
- `county`: County name if present (e.g., "上北郡"), or null
- `city`: City/ward/town/village (e.g., "渋谷区")

### 5. Handle Edge Cases

**No addresses found:**
```json
[]
```
- Inform the user that no Japanese addresses were detected
- Suggest checking if the text contains valid Japanese addresses
- Verify the text format is correct

**Empty or invalid input:**
- Returns empty array `[]`
- Explain to user that input was empty or invalid

**Duplicate addresses:**
- The tool automatically removes duplicates
- Only unique addresses are returned

### 6. Follow-up Processing

After extraction:
- Offer to save results to a file if many addresses were found
- Suggest further processing or analysis if needed
- Ask if user wants detailed breakdown of address components
- Offer to process additional text files

## Examples

### Example 1: Simple Text Extraction

**User request:** "Extract addresses from this text: '本社は東京都渋谷区にあります。支社は大阪府大阪市です。'"

**Steps:**
1. Execute:
```bash
python -c "from extract_address_tool.extract import extract_addresses; text = '本社は東京都渋谷区にあります。支社は大阪府大阪市です。'; print(extract_addresses(text))"
```
2. Parse the JSON result
3. Present:
```
I found 2 addresses in the text:

1. 東京都渋谷区
2. 大阪府大阪市
```

### Example 2: File Processing

**User request:** "Extract all addresses from document.txt"

**Steps:**
1. Read the file first to verify content
2. Execute:
```bash
python -m extract_address_tool.extract document.txt
```
3. Parse and present results with count and list

### Example 3: Detailed Extraction

**User request:** "Extract addresses with detailed information"

**Steps:**
1. Execute:
```bash
python -c "from extract_address_tool.extract import extract_addresses_detailed; text = '青森県上北郡六戸町にあります。'; print(extract_addresses_detailed(text))"
```
2. Parse the structured JSON
3. Present:
```
I found 1 address with the following components:

1. 青森県上北郡六戸町
   - Prefecture: 青森県
   - County: 上北郡
   - City/Town: 六戸町
```

### Example 4: Multiple Address Sources

**User request:** "Find addresses from various prefectures in this document"

**Steps:**
1. Extract addresses from the text
2. Group by prefecture if helpful
3. Present organized results

## Supported Address Formats

The tool can extract:

### Prefecture Types
- **都**: 東京都
- **道**: 北海道
- **府**: 京都府, 大阪府
- **県**: All other prefectures (43 prefectures)

### Administrative Divisions
- **市**: Cities (e.g., 横浜市, 札幌市)
- **区**: Wards (e.g., 渋谷区, 中央区)
- **町**: Towns (e.g., 六戸町)
- **村**: Villages
- **郡**: Counties (e.g., 上北郡)

### Complex Formats
- City + Ward: 横浜市青葉区, 京都市中京区
- Prefecture + County + Town: 青森県上北郡六戸町
- Prefecture + Ward: 東京都渋谷区

## Important Notes

### Features

- **All 47 prefectures**: Supports all Japanese prefectures
- **Duplicate removal**: Automatically removes duplicate addresses
- **Delimiter handling**: Correctly separates addresses split by "と", "や", "、", "。"
- **Unicode support**: Handles all Japanese characters properly

### Limitations

- Only extracts addresses down to city/ward/town/village level
- Does not extract street addresses, building names, or room numbers
- Requires prefecture name to be present (doesn't infer prefecture from city alone)
- Text must contain valid Japanese address formats

### Best Practices

1. **Verify text encoding**: Ensure text is UTF-8 encoded for Japanese characters
2. **Check results**: Review extracted addresses for accuracy
3. **Use detailed mode**: When you need to analyze address components
4. **Process large files**: For very large files, consider processing in chunks
5. **Save results**: For batch processing, offer to save results to JSON file

## Troubleshooting

If extraction fails or returns unexpected results:

1. **Verify module installation**:
   ```bash
   python -c "import extract_address_tool; print('OK')"
   ```

2. **Check text encoding**: Ensure text is properly encoded UTF-8

3. **Test with simple example**:
   ```bash
   python -c "from extract_address_tool.extract import extract_addresses; print(extract_addresses('東京都渋谷区'))"
   ```

4. **Review text format**: Make sure addresses follow Japanese format (prefecture + city/ward/town/village)

5. **Check for special characters**: Some non-standard characters might not be recognized

## Integration with Other Tools

This Skill works well alongside:
- **Read** tool: Read text files before extraction
- **Write** tool: Save extracted addresses to JSON files
- **Grep** tool: Pre-filter text to sections likely containing addresses
- **Glob** tool: Find all text files in a directory for batch processing
- **WebFetch** tool: Extract addresses from web pages

## Testing

Run the comprehensive test suite:
```bash
pytest extract_address_tool/test_extract.py -v
```

All 15 tests should pass, covering:
- Single and multiple address extraction
- Different prefecture types (都/道/府/県)
- Towns and villages with counties (郡)
- Duplicate removal
- Empty input handling
- Complex address formats
