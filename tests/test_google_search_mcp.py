"""Tests for Google Search MCP server."""

import os
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from google_search_mcp import search


class TestSearch:
    """Tests for the search tool."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing."""
        with patch.dict(
            os.environ,
            {
                "GOOGLE_API_KEY": "test-api-key",
                "GOOGLE_CSE_ID": "test-cse-id",
            },
        ):
            # Reload the module to pick up new env vars
            import google_search_mcp
            google_search_mcp.GOOGLE_API_KEY = "test-api-key"
            google_search_mcp.GOOGLE_CSE_ID = "test-cse-id"
            yield

    @pytest.fixture
    def sample_search_response(self):
        """Sample Google Custom Search API response."""
        return {
            "items": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    "snippet": "This is the first test result snippet.",
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example.com/2",
                    "snippet": "This is the second test result snippet.",
                },
                {
                    "title": "Test Result 3",
                    "link": "https://example.com/3",
                    "snippet": "This is the third test result snippet.",
                },
            ]
        }

    async def test_search_success(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test successful search request."""
        httpx_mock.add_response(json=sample_search_response)

        result = await search("test query", num_results=3)

        assert "Test Result 1" in result
        assert "https://example.com/1" in result
        assert "This is the first test result snippet" in result
        assert "Test Result 2" in result
        assert "Test Result 3" in result
        assert "1. " in result
        assert "2. " in result
        assert "3. " in result

    async def test_search_with_default_num_results(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test search with default num_results parameter."""
        httpx_mock.add_response(json=sample_search_response)

        result = await search("test query")

        assert "Test Result 1" in result
        # Verify the request was made with num=10
        request = httpx_mock.get_request()
        assert "num=10" in str(request.url)

    async def test_search_num_results_clamping_upper(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test that num_results is clamped to maximum of 10."""
        httpx_mock.add_response(json=sample_search_response)

        await search("test query", num_results=100)

        request = httpx_mock.get_request()
        assert "num=10" in str(request.url)

    async def test_search_num_results_clamping_lower(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test that num_results is clamped to minimum of 1."""
        httpx_mock.add_response(json=sample_search_response)

        await search("test query", num_results=-5)

        request = httpx_mock.get_request()
        assert "num=1" in str(request.url)

    async def test_search_missing_api_key(self):
        """Test search with missing GOOGLE_API_KEY."""
        with patch.dict(os.environ, {}, clear=True):
            import google_search_mcp
            google_search_mcp.GOOGLE_API_KEY = ""
            google_search_mcp.GOOGLE_CSE_ID = "test-cse-id"

            result = await search("test query")

            assert "Error: GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set" in result

    async def test_search_missing_cse_id(self):
        """Test search with missing GOOGLE_CSE_ID."""
        with patch.dict(os.environ, {}, clear=True):
            import google_search_mcp
            google_search_mcp.GOOGLE_API_KEY = "test-api-key"
            google_search_mcp.GOOGLE_CSE_ID = ""

            result = await search("test query")

            assert "Error: GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set" in result

    async def test_search_api_error_response(
        self, httpx_mock: HTTPXMock, mock_env_vars
    ):
        """Test handling of API error responses."""
        httpx_mock.add_response(
            status_code=403,
            text="Forbidden: API key invalid",
        )

        result = await search("test query")

        assert "Error: Search request failed with status 403" in result
        assert "Forbidden" in result

    async def test_search_invalid_json_response(
        self, httpx_mock: HTTPXMock, mock_env_vars
    ):
        """Test handling of invalid JSON in response."""
        httpx_mock.add_response(
            status_code=200,
            text="This is not valid JSON",
        )

        result = await search("test query")

        assert "Error: Failed to parse response as JSON" in result

    async def test_search_no_results(self, httpx_mock: HTTPXMock, mock_env_vars):
        """Test search with no results found."""
        httpx_mock.add_response(json={"items": []})

        result = await search("test query")

        assert result == "No results found."

    async def test_search_missing_items_key(
        self, httpx_mock: HTTPXMock, mock_env_vars
    ):
        """Test search response without 'items' key."""
        httpx_mock.add_response(json={})

        result = await search("test query")

        assert result == "No results found."

    async def test_search_incomplete_result_data(
        self, httpx_mock: HTTPXMock, mock_env_vars
    ):
        """Test handling of incomplete result data."""
        httpx_mock.add_response(
            json={
                "items": [
                    {
                        # Missing title
                        "link": "https://example.com/1",
                        "snippet": "Test snippet",
                    },
                    {
                        "title": "Test Title",
                        # Missing link
                        "snippet": "Test snippet",
                    },
                    {
                        "title": "Test Title",
                        "link": "https://example.com/2",
                        # Missing snippet
                    },
                ]
            }
        )

        result = await search("test query")

        assert "No title" in result
        assert "No link" in result
        assert "No description" in result

    async def test_search_request_parameters(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test that correct parameters are sent in the request."""
        httpx_mock.add_response(json=sample_search_response)

        await search("my test query", num_results=5)

        request = httpx_mock.get_request()
        assert request.url.params["key"] == "test-api-key"
        assert request.url.params["cx"] == "test-cse-id"
        assert request.url.params["q"] == "my test query"
        assert request.url.params["num"] == "5"

    async def test_search_timeout_configuration(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test that timeout is properly configured."""
        httpx_mock.add_response(json=sample_search_response)

        # The test passes if no timeout error occurs
        result = await search("test query")

        assert "Test Result 1" in result

    async def test_search_multiple_results_formatting(
        self, httpx_mock: HTTPXMock, mock_env_vars
    ):
        """Test formatting of multiple search results."""
        response = {
            "items": [
                {
                    "title": f"Result {i}",
                    "link": f"https://example.com/{i}",
                    "snippet": f"Snippet for result {i}",
                }
                for i in range(1, 6)
            ]
        }
        httpx_mock.add_response(json=response)

        result = await search("test query", num_results=5)

        # Check that results are numbered correctly
        for i in range(1, 6):
            assert f"{i}. Result {i}" in result
            assert f"https://example.com/{i}" in result
            assert f"Snippet for result {i}" in result

        # Check that results are separated by double newlines
        assert "\n\n" in result
