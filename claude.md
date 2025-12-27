# google-search-mcp

A Model Context Protocol (MCP) server that provides Google Custom Search capabilities to LLMs.

## Project Overview

This is a Python-based MCP server that integrates Google Custom Search Engine (CSE) API to enable LLMs to search the web in real-time. The server is built using the FastMCP framework and exposes a single `search` tool.

## Project Structure

```
google-search-mcp/
├── google_search_mcp/
│   ├── __init__.py          # Main MCP server implementation
│   └── __main__.py          # Module entry point for python -m
├── tests/
│   ├── __init__.py          # Test package initialization
│   └── test_google_search_mcp.py  # Comprehensive test suite
├── .env.example             # Environment variable template
├── pyproject.toml           # Project configuration and dependencies
├── README.md                # User documentation
├── LICENSE                  # MIT License
├── claude.md                # Developer documentation
└── .gitignore              # Git ignore rules (includes .env)
```

## Key Files

### google_search_mcp/__init__.py

Main server implementation containing:
- `.env` file loading via `python-dotenv`
- MCP server initialization using FastMCP
- `search` tool implementation
- Environment variable configuration for Google API credentials
- Error handling for API requests

### google_search_mcp/__main__.py

Module entry point that allows running the server with `python -m google_search_mcp`. This is required for Claude Desktop integration.

### .env.example

Template file for environment variable configuration. Copy this to `.env` and fill in your credentials.

## Development Setup

### Prerequisites

1. Python 3.10 or higher
2. Google Custom Search API credentials:
   - API Key from [Google Cloud Console](https://console.cloud.google.com/)
   - Custom Search Engine ID from [Programmable Search Engine](https://programmablesearchengine.google.com/)

### Installation

Install in development mode:
```bash
pip install -e .
```

### Environment Variables

Required environment variables:
- `GOOGLE_API_KEY`: Your Google API key
- `GOOGLE_CSE_ID`: Your Custom Search Engine ID

**Recommended: Using .env file**

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit the `.env` file with your credentials:
```env
GOOGLE_API_KEY=your-api-key
GOOGLE_CSE_ID=your-cse-id
```

The server automatically loads environment variables from `.env` using `python-dotenv`.

**Alternative: Export environment variables**

```bash
export GOOGLE_API_KEY="your-api-key"
export GOOGLE_CSE_ID="your-cse-id"
```

## Dependencies

Core dependencies (defined in pyproject.toml):
- `mcp>=1.0.0`: Model Context Protocol framework
- `httpx>=0.28.0`: Async HTTP client for API requests
- `python-dotenv>=1.0.0`: Load environment variables from .env files

Development dependencies (optional, for testing):
- `pytest>=8.0.0`: Testing framework
- `pytest-asyncio>=0.23.0`: Async support for pytest
- `pytest-httpx>=0.30.0`: HTTP request mocking for httpx

## Architecture

### MCP Server

The server uses FastMCP, a high-level framework for building MCP servers. It provides a single tool:

**Tool: search**
- **Purpose**: Performs web searches using Google Custom Search API
- **Parameters**:
  - `query` (str, required): Search query string
  - `num_results` (int, optional): Number of results (1-10, default 10)
- **Returns**: Formatted text with search results including title, URL, and snippet

### API Integration

- Uses Google Custom Search JSON API (v1)
- Endpoint: `https://www.googleapis.com/customsearch/v1`
- Timeout: 30 seconds for HTTP requests
- Response format: JSON parsed into readable text format

## Code Guidelines

### Error Handling

The code includes error handling for:
- Missing environment variables
- HTTP request failures (non-200 status codes)
- JSON parsing errors
- Empty search results

### Input Validation

- `num_results` is automatically clamped to the range 1-10

### Async Pattern

The `search` tool is async and uses `httpx.AsyncClient` for non-blocking HTTP requests.

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
pytest --cov=google_search_mcp --cov-report=html
```

### Test Structure

The test suite (tests/test_google_search_mcp.py) includes comprehensive tests for:

**Successful Operations:**
- Successful search requests with valid responses
- Default parameter handling
- Multiple results formatting

**Input Validation:**
- num_results clamping (upper bound: 10)
- num_results clamping (lower bound: 1)
- Request parameter verification

**Error Handling:**
- Missing GOOGLE_API_KEY environment variable
- Missing GOOGLE_CSE_ID environment variable
- API error responses (non-200 status codes)
- Invalid JSON in API responses
- Empty search results
- Missing 'items' key in response
- Incomplete result data (missing title/link/snippet)

**Configuration:**
- HTTP client timeout configuration
- Correct API parameters in requests

### Writing New Tests

When adding new functionality:

1. Create test methods in the TestSearch class
2. Use pytest fixtures for common setup:
   - `mock_env_vars`: Mocks environment variables
   - `sample_search_response`: Provides sample API response
   - `httpx_mock`: Mocks HTTP requests (from pytest-httpx)

3. Follow the async pattern:
   ```python
   async def test_new_feature(self, httpx_mock, mock_env_vars):
       httpx_mock.add_response(json={"items": []})
       result = await search("query")
       assert expected_condition
   ```

4. Test both success and failure cases
5. Verify error messages are user-friendly

### Manual Testing

Run the server directly:
```bash
python -m google_search_mcp
```

Or use the installed command:
```bash
google-search-mcp
```

### Testing with Claude Desktop

Add to Claude Desktop configuration:

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
        "GOOGLE_CSE_ID": "your-cse-id"
      }
    }
  }
}
```

**For Windows:**

If `python` is in your PATH, use the same configuration as macOS/Linux. Otherwise, use the full path to Python:

```bash
python -c "import sys; print(sys.executable)"
```

Example configuration with full path:
```json
{
  "mcpServers": {
    "google-search": {
      "command": "C:\\Users\\YOUR_USERNAME\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\\python.exe",
      "args": ["-m", "google_search_mcp"],
      "env": {
        "GOOGLE_API_KEY": "your-api-key",
        "GOOGLE_CSE_ID": "your-cse-id"
      }
    }
  }
}
```

Or if `python` is in PATH:
```json
{
  "mcpServers": {
    "google-search": {
      "command": "python",
      "args": ["-m", "google_search_mcp"],
      "env": {
        "GOOGLE_API_KEY": "your-api-key",
        "GOOGLE_CSE_ID": "your-cse-id"
      }
    }
  }
}
```

**Important for Windows users:** Do NOT use `node` or try to run `build/index.js` - this is a Python package, not a Node.js package.

## Common Issues and Solutions

### "Error: Cannot find module 'D:\workspace\google-search-mcp\build\index.js'" (Windows)

**Problem:** Claude Desktop is trying to run the server with Node.js instead of Python.

**Solution:** This is a Python package, not a Node.js package. Update your Claude Desktop config:
1. Find your Python executable path: `python -c "import sys; print(sys.executable)"`
2. Update the config to use Python (or the full path)
3. Use args: `["-m", "google_search_mcp"]`

See the "Testing with Claude Desktop" section above for the correct configuration.

### "Cannot read properties of undefined (reading 'cmd')"

**Problem:** Claude Desktop configuration parsing error.

**Solution:**
1. Make sure `__main__.py` exists in the `google_search_mcp` directory
2. Verify the package is installed: `pip show google-search-mcp`
3. Test manual execution: `python -m google_search_mcp`
4. Use simple `"command": "python"` instead of full paths if possible
5. Restart Claude Desktop after changing configuration

### "No module named google_search_mcp"

**Problem:** The Python installation that Claude Desktop is using doesn't have the package installed.

**Solution:**
1. Check which Python Claude Desktop is using from the logs
2. Find where the package is installed: `python -m pip show google-search-mcp` (look at "Location")
3. Use the full path to the correct Python executable in your config
4. Example: If the package is installed in the WindowsApps Python, use:
   ```
   C:\\Users\\USERNAME\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_...\\python.exe
   ```

**Note:** Windows can have multiple Python installations. Make sure the config uses the same Python where you installed the package.

### "Error: GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set"

- Ensure both environment variables are properly set before running the server
- In Claude Desktop config, verify the env object contains both keys
- If using `.env` file, make sure it's in the correct directory and properly formatted

### Search Request Failures

- Check API key validity and quota limits in Google Cloud Console
- Verify CSE ID is correct
- Check network connectivity

### Timeout Errors

- Current timeout is 30 seconds
- If experiencing timeouts, consider network conditions or API response times

## Making Changes

### Adding New Tools

To add new tools to the server:
1. Define a new async function in `__init__.py`
2. Decorate it with `@mcp.tool()`
3. Include proper docstring with Args and Returns sections
4. Update README.md to document the new tool

### Modifying Search Results Format

The search results formatting is in google_search_mcp/__init__.py:60-66. When modifying:
- Maintain structured output for LLM parsing
- Include title, URL, and snippet for each result
- Consider token usage for LLM context

### Updating Dependencies

Dependencies are managed in pyproject.toml. When updating:
- Update the version constraint in the dependencies list
- Test thoroughly with the new version
- Update requires-python if Python version requirements change

## Release Process

1. Update version in pyproject.toml
2. Update README.md with any new features or changes
3. Commit changes
4. Create a git tag for the version
5. Build and publish to PyPI:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## Best Practices

- Keep the server lightweight and focused on search functionality
- Validate all inputs before making API requests
- Provide clear error messages to help users troubleshoot
- Maintain backward compatibility when making changes
- Document any breaking changes clearly in release notes
