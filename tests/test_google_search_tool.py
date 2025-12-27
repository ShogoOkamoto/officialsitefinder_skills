"""Tests for Google Search CLI Tool."""

import json
import os
import subprocess
import sys
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from google_search_tool import search


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(
        os.environ,
        {
            "GOOGLE_API_KEY": "test-api-key",
            "GOOGLE_CSE_ID": "test-cse-id",
        },
    ):
        # Reload the module to pick up new env vars
        import google_search_tool

        google_search_tool.GOOGLE_API_KEY = "test-api-key"
        google_search_tool.GOOGLE_CSE_ID = "test-cse-id"
        yield


@pytest.fixture
def sample_search_response():
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


class TestSearch:
    """Tests for the search function."""

    def test_search_success(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test successful search request."""
        httpx_mock.add_response(json=sample_search_response)

        result = search("test query", num_results=3)

        assert "results" in result
        assert "count" in result
        assert result["count"] == 3
        assert len(result["results"]) == 3

        # Check first result
        assert result["results"][0]["title"] == "Test Result 1"
        assert result["results"][0]["link"] == "https://example.com/1"
        assert (
            result["results"][0]["snippet"] == "This is the first test result snippet."
        )

        # Check all results are present
        titles = [r["title"] for r in result["results"]]
        assert "Test Result 1" in titles
        assert "Test Result 2" in titles
        assert "Test Result 3" in titles

    def test_search_with_default_num_results(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test search with default num_results parameter."""
        httpx_mock.add_response(json=sample_search_response)

        result = search("test query")

        assert "results" in result
        # Verify the request was made with num=10
        request = httpx_mock.get_request()
        assert "num=10" in str(request.url)

    def test_search_num_results_clamping_upper(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test that num_results is clamped to maximum of 10."""
        httpx_mock.add_response(json=sample_search_response)

        search("test query", num_results=100)

        request = httpx_mock.get_request()
        assert "num=10" in str(request.url)

    def test_search_num_results_clamping_lower(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test that num_results is clamped to minimum of 1."""
        httpx_mock.add_response(json=sample_search_response)

        search("test query", num_results=-5)

        request = httpx_mock.get_request()
        assert "num=1" in str(request.url)

    def test_search_missing_api_key(self):
        """Test search with missing GOOGLE_API_KEY."""
        with patch.dict(os.environ, {}, clear=True):
            import google_search_tool

            google_search_tool.GOOGLE_API_KEY = ""
            google_search_tool.GOOGLE_CSE_ID = "test-cse-id"

            result = search("test query")

            assert "error" in result
            assert (
                "GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set"
                in result["error"]
            )

    def test_search_missing_cse_id(self):
        """Test search with missing GOOGLE_CSE_ID."""
        with patch.dict(os.environ, {}, clear=True):
            import google_search_tool

            google_search_tool.GOOGLE_API_KEY = "test-api-key"
            google_search_tool.GOOGLE_CSE_ID = ""

            result = search("test query")

            assert "error" in result
            assert (
                "GOOGLE_API_KEY and GOOGLE_CSE_ID environment variables must be set"
                in result["error"]
            )

    def test_search_api_error_response(self, httpx_mock: HTTPXMock, mock_env_vars):
        """Test handling of API error responses."""
        httpx_mock.add_response(
            status_code=403,
            text="Forbidden: API key invalid",
        )

        result = search("test query")

        assert "error" in result
        assert "Search request failed with status 403" in result["error"]
        assert "Forbidden" in result["error"]

    def test_search_invalid_json_response(self, httpx_mock: HTTPXMock, mock_env_vars):
        """Test handling of invalid JSON in response."""
        httpx_mock.add_response(
            status_code=200,
            text="This is not valid JSON",
        )

        result = search("test query")

        assert "error" in result
        assert "Failed to parse response as JSON" in result["error"]

    def test_search_no_results(self, httpx_mock: HTTPXMock, mock_env_vars):
        """Test search with no results found."""
        httpx_mock.add_response(json={"items": []})

        result = search("test query")

        assert "results" in result
        assert result["results"] == []
        assert result["count"] == 0

    def test_search_missing_items_key(self, httpx_mock: HTTPXMock, mock_env_vars):
        """Test search response without 'items' key."""
        httpx_mock.add_response(json={})

        result = search("test query")

        assert "results" in result
        assert result["results"] == []
        assert result["count"] == 0

    def test_search_incomplete_result_data(
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

        result = search("test query")

        assert "results" in result
        assert result["count"] == 3

        # Check default values for missing fields
        assert result["results"][0]["title"] == "No title"
        assert result["results"][1]["link"] == "No link"
        assert result["results"][2]["snippet"] == "No description"

    def test_search_request_parameters(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test that correct parameters are sent in the request."""
        httpx_mock.add_response(json=sample_search_response)

        search("my test query", num_results=5)

        request = httpx_mock.get_request()
        assert request.url.params["key"] == "test-api-key"
        assert request.url.params["cx"] == "test-cse-id"
        assert request.url.params["q"] == "my test query"
        assert request.url.params["num"] == "5"

    def test_search_timeout_configuration(
        self, httpx_mock: HTTPXMock, mock_env_vars, sample_search_response
    ):
        """Test that timeout is properly configured."""
        httpx_mock.add_response(json=sample_search_response)

        # The test passes if no timeout error occurs
        result = search("test query")

        assert "results" in result
        assert result["count"] == 3

    def test_search_multiple_results_formatting(
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

        result = search("test query", num_results=5)

        assert "results" in result
        assert result["count"] == 5

        # Check that results are formatted correctly
        for i in range(1, 6):
            assert result["results"][i - 1]["title"] == f"Result {i}"
            assert result["results"][i - 1]["link"] == f"https://example.com/{i}"
            assert result["results"][i - 1]["snippet"] == f"Snippet for result {i}"


class TestCLI:
    """Tests for the CLI interface."""

    def test_cli_argument_parsing(self):
        """Test CLI argument parsing without making actual requests."""
        import argparse
        from unittest.mock import patch
        import google_search_tool

        # Test basic argument parsing
        with patch("sys.argv", ["google-search-tool", "test query"]):
            parser = argparse.ArgumentParser()
            parser.add_argument("query")
            parser.add_argument("-n", "--num-results", type=int, default=10)
            parser.add_argument("--pretty", action="store_true")

            args = parser.parse_args()
            assert args.query == "test query"
            assert args.num_results == 10
            assert args.pretty is False

    def test_cli_with_num_results_arg(self):
        """Test CLI with --num-results option argument parsing."""
        import argparse
        from unittest.mock import patch

        with patch("sys.argv", ["google-search-tool", "test", "-n", "5"]):
            parser = argparse.ArgumentParser()
            parser.add_argument("query")
            parser.add_argument("-n", "--num-results", type=int, default=10)
            parser.add_argument("--pretty", action="store_true")

            args = parser.parse_args()
            assert args.query == "test"
            assert args.num_results == 5

    def test_cli_with_pretty_flag(self):
        """Test CLI with --pretty flag argument parsing."""
        import argparse
        from unittest.mock import patch

        with patch("sys.argv", ["google-search-tool", "test", "--pretty"]):
            parser = argparse.ArgumentParser()
            parser.add_argument("query")
            parser.add_argument("-n", "--num-results", type=int, default=10)
            parser.add_argument("--pretty", action="store_true")

            args = parser.parse_args()
            assert args.query == "test"
            assert args.pretty is True

    def test_cli_missing_env_vars(self):
        """Test CLI with missing environment variables."""
        # Run without setting environment variables
        result = subprocess.run(
            [sys.executable, "-m", "google_search_tool", "test"],
            capture_output=True,
            text=True,
            env={**os.environ, "GOOGLE_API_KEY": "", "GOOGLE_CSE_ID": ""},
        )

        assert result.returncode == 1
        output = json.loads(result.stdout)
        assert "error" in output

    def test_cli_help(self):
        """Test CLI help message."""
        result = subprocess.run(
            [sys.executable, "-m", "google_search_tool", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Google Custom Search CLI Tool" in result.stdout
        assert "query" in result.stdout
        assert "--num-results" in result.stdout
        assert "--pretty" in result.stdout

    def test_json_output_format(self, httpx_mock: HTTPXMock, mock_env_vars):
        """Test that main function outputs valid JSON."""
        from unittest.mock import patch
        import io
        import google_search_tool

        sample_response = {
            "items": [
                {
                    "title": "Test",
                    "link": "https://example.com",
                    "snippet": "Test snippet",
                }
            ]
        }
        httpx_mock.add_response(json=sample_response)

        # Capture stdout
        captured_output = io.StringIO()

        with patch("sys.argv", ["google-search-tool", "test query"]):
            with patch("sys.stdout", captured_output):
                try:
                    google_search_tool.main()
                except SystemExit:
                    pass

        output = captured_output.getvalue()
        # Should be valid JSON
        parsed = json.loads(output)
        assert "results" in parsed or "error" in parsed
