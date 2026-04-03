# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python MCP (Model Context Protocol) server that provides Google Custom Search capabilities. Built with FastMCP framework, it exposes a single async `search` tool that queries the Google Custom Search API.

## Development Commands

### Setup

```bash
# Install in development mode (run from parent directory)
pip install -e .

# Install with dev dependencies for testing
pip install -e ".[dev]"

# Copy environment template and configure
cp .env.example .env
# Then edit .env with your GOOGLE_API_KEY and GOOGLE_CSE_ID
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=google_search_mcp --cov-report=html

# Test the MCP server specifically
pytest tests/test_google_search_mcp.py -v
```

### Running the Server

```bash
# Using module entry point
python -m google_search_mcp

# Using installed script (if installed)
google-search-mcp
```

## Architecture

### Core Components

**`__init__.py`** (80 lines) - Main server implementation
- Lines 1-14: Imports and environment setup with `python-dotenv`
- Lines 16-17: FastMCP server initialization
- Lines 19-22: Google API configuration from environment variables
- Lines 25-70: `@mcp.tool()` decorated async `search()` function
  - Lines 36-37: Environment variable validation
  - Lines 39: Input clamping (num_results: 1-10)
  - Lines 48-62: HTTP request with httpx.AsyncClient (30s timeout)
  - Lines 64-70: Result formatting as numbered list with title/URL/snippet
- Lines 73-79: `main()` entry point that calls `mcp.run()`

**`__main__.py`** (7 lines) - Module execution entry point
- Imports and calls `main()` from `__init__.py`
- Required for `python -m google_search_mcp` to work

### Key Design Patterns

**Async HTTP Client**: Uses `httpx.AsyncClient` with 30-second timeout for non-blocking API requests.

**Environment Configuration**: Relies on `python-dotenv` to load `.env` file automatically. Environment variables (`GOOGLE_API_KEY`, `GOOGLE_CSE_ID`) are loaded at module import time.

**Error Handling Strategy**:
- Environment variables: Returns error string if missing
- HTTP errors: Returns formatted error with status code and response text
- JSON parsing: Catches `ValueError` and returns error message
- Empty results: Returns "No results found." message

**Input Validation**: `num_results` is clamped using `max(1, min(10, num_results))` to enforce Google CSE limits.

## Testing Architecture

Tests use pytest with async support (`pytest-asyncio`) and HTTP mocking (`pytest-httpx`).

**Test Fixtures** (defined in test file):
- `mock_env_vars`: Mocks environment variables for all tests
- `sample_search_response`: Provides valid API response structure
- `httpx_mock`: HTTP request mocker from pytest-httpx plugin

**Test Coverage Categories**:
1. Successful operations (valid responses, default parameters, multiple results)
2. Input validation (num_results clamping at bounds)
3. Error handling (missing env vars, HTTP errors, JSON parsing, empty results)
4. Configuration verification (timeout, API parameters)

## Environment Variables

Required for operation:
- `GOOGLE_API_KEY`: Google Cloud API key for Custom Search API
- `GOOGLE_CSE_ID`: Custom Search Engine ID from Programmable Search Engine

The server checks these at runtime (not import time) and returns error messages if missing.

## Integration Notes

### Claude Desktop Configuration

This package must be run with Python (not Node.js). The correct configuration uses:
- `"command": "python"` (or full path to Python executable)
- `"args": ["-m", "google_search_mcp"]`
- `"env"` object with both API credentials

Common Windows issue: Multiple Python installations. Ensure Claude Desktop uses the same Python where the package is installed. Find the correct path with:
```bash
python -c "import sys; print(sys.executable)"
```

### Claude Code MCP Integration

```bash
claude mcp add --transport stdio google-search --scope project \
  --env GOOGLE_API_KEY=your-api-key \
  --env GOOGLE_CSE_ID=your-cse-id \
  -- python -m google_search_mcp
```

## API Constraints

- **Rate Limits**: Google Custom Search API has quota limits (check Google Cloud Console)
- **Results Limit**: Maximum 10 results per request (enforced by input validation)
- **Timeout**: HTTP requests timeout after 30 seconds
- **Response Format**: Returns formatted text, not JSON (for LLM consumption)

## Making Changes

### Adding New Tools

1. Define async function in `__init__.py`
2. Decorate with `@mcp.tool()`
3. Include docstring with `Args:` and `Returns:` sections (FastMCP uses these)
4. Add corresponding tests in `tests/test_google_search_mcp.py`

### Modifying Response Format

The result formatting logic is at `__init__.py:64-70`. Current format is numbered list with title, URL, and snippet. Consider token usage when modifying - this output is consumed by LLMs.

### Updating Dependencies

Dependencies are in `pyproject.toml` at parent directory level. This package shares dependencies with sibling packages (`google_search_tool`, etc.).
