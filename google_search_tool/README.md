# google-search-tool

A command-line executable Google search tool. Returns search results in JSON format.

## Overview

`google-search-tool` is a command-line tool that performs web searches using the Google Custom Search Engine (CSE) API and returns results in JSON format.

## Features

- Simple command-line interface
- JSON format result output
- Errors also returned in JSON format
- Configurable number of search results (1-10 items)
- Pretty-print option for readable output

## Installation

Run the following in the project root directory:

```bash
pip install -e .
```

## Environment Variable Setup

Google Custom Search API credentials are required:

1. Copy `.env.example` to create a `.env` file
2. Set the following environment variables:

```env
GOOGLE_API_KEY=your-api-key
GOOGLE_CSE_ID=your-cse-id
```

### How to Obtain Google API Keys

1. **API Key**: Obtain from [Google Cloud Console](https://console.cloud.google.com/)
2. **CSE ID**: Create at [Programmable Search Engine](https://programmablesearchengine.google.com/)

## Usage

### Basic Usage

```bash
# Recommended: Run with python -m
python -m google_search_tool "search query"
```

### Options

```bash
# Specify number of results (1-10 items, default: 10)
python -m google_search_tool "search query" -n 5
python -m google_search_tool "search query" --num-results 5

# Pretty-print for readable output
python -m google_search_tool "search query" --pretty

# Combine options
python -m google_search_tool "Python programming" -n 3 --pretty
```

### Display Help

```bash
python -m google_search_tool --help
```

## Output Format

### JSON Output on Success

```json
{
  "results": [
    {
      "title": "Search result title",
      "link": "https://example.com",
      "snippet": "Search result description"
    }
  ],
  "count": 1
}
```

### JSON Output on Error

```json
{
  "error": "Error message"
}
```

### When No Results Found

```json
{
  "results": [],
  "count": 0
}
```

## Usage Examples

### Basic Search

```bash
$ python -m google_search_tool "Python programming"
{"results": [{"title": "Welcome to Python.org", "link": "https://www.python.org/", "snippet": "The official home of the Python Programming Language."}], "count": 1}
```

### Pretty-print for Readability

```bash
$ python -m google_search_tool "Python programming" --pretty
{
  "results": [
    {
      "title": "Welcome to Python.org",
      "link": "https://www.python.org/",
      "snippet": "The official home of the Python Programming Language."
    }
  ],
  "count": 1
}
```

### Specify Number of Results

```bash
$ python -m google_search_tool "machine learning" -n 3 --pretty
{
  "results": [
    {
      "title": "Machine Learning - Wikipedia",
      "link": "https://en.wikipedia.org/wiki/Machine_learning",
      "snippet": "Machine learning is a field of study in artificial intelligence..."
    },
    {
      "title": "What is Machine Learning? | IBM",
      "link": "https://www.ibm.com/topics/machine-learning",
      "snippet": "Machine learning is a branch of AI and computer science..."
    },
    {
      "title": "Introduction to Machine Learning",
      "link": "https://developers.google.com/machine-learning/intro-to-ml",
      "snippet": "This course introduces the foundational concepts of machine learning..."
    }
  ],
  "count": 3
}
```

## Programmatic Usage

You can also use it directly from Python programs:

```python
from google_search_tool import search

# Execute search
result = search("Python programming", num_results=5)

# Check results
if "error" in result:
    print(f"Error: {result['error']}")
else:
    print(f"Search results: {result['count']} items")
    for item in result["results"]:
        print(f"- {item['title']}: {item['link']}")
```

## Error Handling

The tool returns errors in the following cases:

1. **Environment variables not set**: `GOOGLE_API_KEY` or `GOOGLE_CSE_ID` is not configured
2. **API error**: Error response returned from Google API
3. **Timeout**: Request times out after 30 seconds
4. **Network error**: Connection failed

On error, the tool exits with exit code `1`.

## Testing

To run tests:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/test_google_search_tool.py

# Verbose output
pytest tests/test_google_search_tool.py -v

# Coverage report
pytest tests/test_google_search_tool.py --cov=google_search_tool
```

## License

MIT License
