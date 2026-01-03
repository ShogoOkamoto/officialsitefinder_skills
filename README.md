# Official Site Finder - Automated Japanese Facility Website Discovery

A sophisticated multi-tool ecosystem for automatically discovering official websites of Japanese facilities using Google search, address extraction, HTML analysis, and Claude Code subagent judgment.

## What is Official Site Finder?

Official Site Finder is a comprehensive system designed to automatically discover and verify official websites for Japanese facilities (businesses, organizations, tourist attractions, etc.). The system combines multiple specialized tools to ensure accurate results through address-based verification.

**Use Case**: Given a facility name and address, the system searches Google, downloads web pages, extracts and matches addresses, and uses AI-powered judgment to identify the official website's top page.

**v4 Innovation**: Uses Claude Code's built-in subagent functionality for top-page verification, eliminating direct Claude API calls and associated costs while maintaining high accuracy.

## Key Features

- ✅ **Address-based accuracy verification** - Confirms official sites by matching addresses on web pages
- ✅ **Automated 6-tool integration workflow** - Seamlessly orchestrates search, extraction, and verification
- ✅ **Claude Code skill integration** - Easy to use via `/officialsite-finder` command
- ✅ **Cost-efficient** - No direct Claude API calls (v4 improvement)
- ✅ **Support for various Japanese facilities** - Works with businesses, organizations, tourist sites, etc.

## Tool Ecosystem Overview

The Official Site Finder System consists of 6 core tools and 3 Claude Code skills working together:

```
Official Site Finder System
├── officialsite_finder_tool (Main Integration)
│   └── Orchestrates:
│       ├── google_search_tool (Web Search)
│       ├── extract_address_tool (Address Extraction)
│       ├── compare_address_tool (Address Matching)
│       └── playwright_download_tool (HTML Download)
├── Claude Skills (.claude/skills/)
│   ├── officialsite_finder_skill ⭐ PRIMARY
│   ├── google_search_skill
│   └── extract_address_skill
└── MCP Server
    └── google_search_mcp
```

## Quick Start

### Using Claude Code Skill (Recommended)

The easiest way to use Official Site Finder is through the Claude Code skill:

```bash
/officialsite-finder
```

Claude Code will ask for the facility name and address, then automatically run the complete workflow.

### Using CLI Directly

You can also run the main tool directly from the command line:

```bash
python -m officialsite_finder_tool --name "東京タワー" --address "東京都港区芝公園4-2-8"
```

### Expected Output

**Success:**
```json
{
  "success": true,
  "facility_name": "東京タワー",
  "input_address": "東京都港区芝公園4-2-8",
  "official_site_url": "https://www.tokyotower.co.jp/",
  "matched_address": "東京都港区",
  "message": "公式サイトのトップページを発見しました"
}
```

**Failure:**
```json
{
  "success": false,
  "facility_name": "Unknown Facility",
  "input_address": "Unknown Address",
  "message": "公式サイトが見つかりませんでした"
}
```

## Installation

### Prerequisites

- **Python 3.10 or higher**
- **Google Custom Search API credentials:**
  - API Key from [Google Cloud Console](https://console.cloud.google.com/)
  - Custom Search Engine ID from [Programmable Search Engine](https://programmablesearchengine.google.com/)

### Install

```bash
# Clone or navigate to the repository
cd officialsitefinder_skills

# Install in development mode
pip install -e .
```

### Environment Setup

1. Create a `.env` file from the template:

```bash
cp .env.example .env
```

2. Edit the `.env` file and add your Google API credentials:

```env
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_CSE_ID=your-custom-search-engine-id-here
```

#### Getting Google API Credentials

**Step 1: Create a Google Cloud Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Custom Search API**

**Step 2: Create an API Key**
1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the API key to your `.env` file

**Step 3: Create a Custom Search Engine**
1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Configure to search the entire web
4. Copy the "Search Engine ID" to your `.env` file

## How It Works (High-Level)

The Official Site Finder follows this workflow:

1. **Extract address components** from the input (e.g., "東京都港区芝公園4-2-8" → "東京都港区")
2. **Google search** using query: "{facility_name} {address}"
3. **Download HTML** from top 5 search results
4. **Extract addresses** from each downloaded page
5. **Match addresses** between input and page content
6. **Verify top page** using Claude Code subagent (if needed)
7. **Return result** with official site URL or error message

For detailed workflow and architecture, see [CLAUDE.md](CLAUDE.md).

## Architecture

Official Site Finder uses a modular architecture where each tool can operate independently or as part of the integrated workflow. The system is designed for:

- **Modularity**: Each tool has a single, well-defined purpose
- **Composability**: Tools work seamlessly together
- **Extensibility**: Easy to add new tools or modify existing ones
- **Cost Efficiency**: No direct Claude API calls (v4 innovation)

For comprehensive architecture documentation, see [CLAUDE.md](CLAUDE.md).

## Documentation

- 📖 **[CLAUDE.md](CLAUDE.md)**: Developer guide with architecture details, tool descriptions, and development guidelines
- 📋 **[officialsitefinder_skills_v4.md](officialsitefinder_skills_v4.md)**: Complete v4 specification (Japanese)
- 🔧 **Tool-specific docs**: See each tool directory for detailed documentation

## Individual Tools

Each tool can be used independently or as part of the integrated workflow:

### google_search_tool
CLI tool for Google Custom Search with JSON output. Performs web searches and returns structured results.

- **Location**: `google_search_tool/`
- **Usage**: `python -m google_search_tool "query" -n 5`
- **Documentation**: [google_search_tool/README.md](google_search_tool/README.md)

### google_search_mcp
MCP (Model Context Protocol) server for Claude Desktop integration. Provides Google search capability to LLMs.

- **Location**: `google_search_mcp/`
- **Usage**: Configure in Claude Desktop as MCP server
- **Documentation**: [google_search_mcp/README.md](google_search_mcp/README.md)

### extract_address_tool
Extracts Japanese addresses (prefecture to city level) from plain text.

- **Location**: `extract_address_tool/`
- **Usage**: `echo "text" | python -m extract_address_tool.extract`
- **Documentation**: [extract_address_tool/CLAUDE.md](extract_address_tool/CLAUDE.md)

### compare_address_tool
Normalizes and compares Japanese addresses for matching.

- **Location**: `compare_address_tool/`
- **Usage**: `python -m compare_address_tool "addr1" "addr2"`
- **Documentation**: [compare_address_tool/README.md](compare_address_tool/README.md)

### officialsite_finder_tool
Main integration tool that orchestrates all other tools to discover official websites.

- **Location**: `officialsite_finder_tool/`
- **Usage**: `python -m officialsite_finder_tool --name "name" --address "address"`
- **Documentation**: [officialsite_finder_tool/README.md](officialsite_finder_tool/README.md)

### playwright_download_tool
Downloads HTML using Playwright and extracts plain text (legacy tool).

- **Location**: `playwright_download_tool/`
- **Usage**: `python download.py "URL" --format=text`

## Troubleshooting

### Common Issues

#### "Error: Cannot find module 'D:\workspace\google-search-mcp\build\index.js'" (Windows)

**Problem**: Claude Desktop is trying to run the server with Node.js instead of Python.

**Solution**: This is a Python package, not a Node.js package. Update your Claude Desktop configuration:

1. Find your Python executable path:
   ```bash
   python -c "import sys; print(sys.executable)"
   ```

2. Update the config to use Python with the full path or just `python` if it's in your PATH

3. Use args: `["-m", "google_search_mcp"]`

See [google_search_mcp/README.md](google_search_mcp/README.md) for the correct configuration.

#### "No module named 'google_search_mcp'"

**Problem**: The Python installation that Claude Desktop is using doesn't have the package installed.

**Solution**:
1. Check which Python Claude Desktop is using from the logs
2. Find where the package is installed: `python -m pip show google-search-mcp`
3. Use the full path to the correct Python executable in your config

**Note**: Windows can have multiple Python installations. Make sure the config uses the same Python where you installed the package.

#### "Error: GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set"

**Solution**:
- Ensure both environment variables are properly set in your `.env` file
- In Claude Desktop config, verify the `env` object contains both keys
- Check that the `.env` file is in the correct directory (project root)

#### Search Request Failures

**Solution**:
- Check API key validity and quota limits in Google Cloud Console
- Verify CSE ID is correct
- Check network connectivity

For more troubleshooting information, see [CLAUDE.md](CLAUDE.md).

## Version

**Current Version**: v4 (Subagent-based architecture)

**Key Changes in v4**:
- Eliminated direct Claude API calls
- Introduced Claude Code subagent integration
- Removed `ANTHROPIC_API_KEY` requirement
- Cost optimization (no API charges)
- Improved debugging with visible subagent logs

For complete version history, see [officialsitefinder_skills_v4.md](officialsitefinder_skills_v4.md) (Japanese).

## Testing

### Running Tests

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=google_search_mcp --cov=google_search_tool --cov-report=html
```

For detailed testing strategy and guidelines, see [CLAUDE.md](CLAUDE.md).

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! For development guidelines, architecture details, and contribution instructions, please see [CLAUDE.md](CLAUDE.md).

## Related Projects

- **[FastMCP](https://github.com/jlowin/fastmcp)**: Framework used for MCP server implementation
- **[Claude Code](https://claude.com/claude-code)**: CLI tool that powers the skill integration

---

**Note**: This project focuses on Japanese facilities and addresses. Multi-language support is planned for future versions.
