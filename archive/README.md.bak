# google-search-mcp

A Model Context Protocol (MCP) server and command-line tool that utilizes Google Custom Search (CSE) to retrieve information from the internet.

This repository contains two tools:
- **google-search-mcp**: MCP server for LLM integration
- **google-search-tool**: CLI tool that returns JSON results

## Prerequisites

A Google Custom Search API key and Custom Search Engine ID are required:

1. Get a Google API Key from the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a Custom Search Engine at [Programmable Search Engine](https://programmablesearchengine.google.com/)

## Installation

```bash
pip install google-search-mcp
```

Or install from source:

```bash
pip install .
```

## Configuration

Create a `.env` file in the project root directory:

```bash
cp .env.example .env
```

Then edit the `.env` file and add your credentials:

```env
GOOGLE_API_KEY=your-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
```

Alternatively, you can set environment variables directly:

```bash
export GOOGLE_API_KEY="your-api-key"
export GOOGLE_CSE_ID="your-custom-search-engine-id"
```

## Usage

### google-search-mcp (MCP Server)

Run the MCP server:

```bash
google-search-mcp
```

Or with Python module:

```bash
python -m google_search_mcp
```

### google-search-tool (CLI Tool)

Search from command line and get JSON results:

```bash
# Basic search
google-search-tool "your search query"

# Specify number of results (1-10)
google-search-tool "Python programming" -n 5

# Pretty-print JSON output
google-search-tool "machine learning" --pretty

# Combine options
google-search-tool "AI research" -n 3 --pretty
```

**Example output:**

```bash
$ google-search-tool "Python" -n 2 --pretty
{
  "results": [
    {
      "title": "Welcome to Python.org",
      "link": "https://www.python.org/",
      "snippet": "The official home of the Python Programming Language."
    },
    {
      "title": "Python (programming language) - Wikipedia",
      "link": "https://en.wikipedia.org/wiki/Python_(programming_language)",
      "snippet": "Python is a high-level, general-purpose programming language..."
    }
  ],
  "count": 2
}
```

Or use Python module:

```bash
python -m google_search_tool "your search query"
```

### With Claude Desktop

Add the following to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**For macOS/Linux:**

```json
{
  "mcpServers": {
    "google-search": {
      "command": "python",
      "args": ["-m", "google_search_mcp"],
      "env": {
        "GOOGLE_API_KEY": "your-api-key",
        "GOOGLE_CSE_ID": "your-custom-search-engine-id"
      }
    }
  }
}
```

**For Windows:**

If `python` is in your PATH (check with `where python`), you can use the same configuration as macOS/Linux:

```json
{
  "mcpServers": {
    "google-search": {
      "command": "python",
      "args": ["-m", "google_search_mcp"],
      "env": {
        "GOOGLE_API_KEY": "your-api-key",
        "GOOGLE_CSE_ID": "your-custom-search-engine-id"
      }
    }
  }
}
```

If you need to use a specific Python installation, find the full path with:
```bash
python -c "import sys; print(sys.executable)"
```

Then use the full path in the configuration:
```json
{
  "mcpServers": {
    "google-search": {
      "command": "C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
      "args": ["-m", "google_search_mcp"],
      "env": {
        "GOOGLE_API_KEY": "your-api-key",
        "GOOGLE_CSE_ID": "your-custom-search-engine-id"
      }
    }
  }
}
```

**Note:** Environment variables must be set in the Claude Desktop config `env` section for the server to access them.

## Tools

### search

Search the web using Google Custom Search.

**Parameters:**
- `query` (string, required): The search query string
- `num_results` (integer, optional): Number of results to return (1-10, default 10)

## Development

### Running Tests

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run all tests:

```bash
pytest
```

Run tests for specific tool:

```bash
# Test MCP server
pytest tests/test_google_search_mcp.py -v

# Test CLI tool
pytest tests/test_google_search_tool.py -v
```

Run tests with coverage:

```bash
pytest --cov=google_search_mcp --cov=google_search_tool --cov-report=html
```

### Test Coverage

The test suite includes comprehensive tests for both tools:

**google-search-mcp (MCP Server):**
- Successful search requests
- Environment variable validation
- API error handling
- JSON parsing errors
- Empty search results
- Input parameter validation (num_results clamping)
- Result formatting
- Request parameter verification

**google-search-tool (CLI Tool):**
- All search function tests (same as MCP)
- CLI argument parsing
- JSON output format validation
- Command-line option handling (--pretty, -n)
- Help message display
- Exit code validation


### Install

To Use this mcp from ClaudeCode, 
claude mcp add --transport stdio google-search --scope project --env GOOGLE_API_KEY=your-api-key --env GOOGLE_CSE_ID=your-cse-id -- python -m google_search_mcp

or 
  claude mcp add --transport stdio google-search --scope user --env GOOGLE_API_KEY=your-api-key --env GOOGLE_CSE_ID=your-cse-id -- python -m google_search_mcp


## License

MIT License - see [LICENSE](LICENSE) for details.
