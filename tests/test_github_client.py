"""
Tests for GitHub client module.
"""

import pytest
from unittest.mock import Mock, patch
import requests
from context9.github_client import (
    GitHubClient,
    GitHubFileNotFoundError,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubClientError,
)


class TestGitHubClient:
    """Test cases for GitHub client."""

    @pytest.fixture
    def client(self):
        """Create a test GitHub client."""
        return GitHubClient(
            owner="test-owner", repo="test-repo", branch="main", token="test-token"
        )

    def test_init(self, client):
        """Test client initialization."""
        assert client.owner == "test-owner"
        assert client.repo == "test-repo"
        assert client.branch == "main"
        assert client.token == "test-token"
        assert "Authorization" in client.headers

    def test_init_without_token(self):
        """Test client initialization without token."""
        client = GitHubClient(owner="test", repo="test")
        assert "Authorization" not in client.headers

    @patch("remote_doc_mcp.github_client.requests.Session.get")
    def test_read_file_success(self, mock_get, client):
        """Test successful file reading."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "# Test Document\n\nThis is a test."
        mock_get.return_value = mock_response

        content = client.read_file("test.md")

        assert content == "# Test Document\n\nThis is a test."
        mock_get.assert_called_once()

    @patch("remote_doc_mcp.github_client.requests.Session.get")
    def test_read_file_not_found(self, mock_get, client):
        """Test file not found error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with pytest.raises(GitHubFileNotFoundError):
            client.read_file("nonexistent.md")

    @patch("remote_doc_mcp.github_client.requests.Session.get")
    def test_read_file_authentication_error(self, mock_get, client):
        """Test authentication error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with pytest.raises(GitHubAuthenticationError):
            client.read_file("test.md")

    @patch("remote_doc_mcp.github_client.requests.Session.get")
    def test_read_file_rate_limit_error(self, mock_get, client):
        """Test rate limit error."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_get.return_value = mock_response

        with pytest.raises(GitHubRateLimitError):
            client.read_file("test.md")

    @patch("remote_doc_mcp.github_client.requests.Session.get")
    def test_read_file_timeout(self, mock_get, client):
        """Test request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(GitHubClientError, match="timeout"):
            client.read_file("test.md")

    @patch("remote_doc_mcp.github_client.requests.Session.get")
    def test_read_file_with_custom_branch(self, mock_get, client):
        """Test reading file from custom branch."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "content"
        mock_get.return_value = mock_response

        client.read_file("test.md", branch="develop")

        # Check that branch parameter was passed
        call_args = mock_get.call_args
        assert call_args[1]["params"]["ref"] == "develop"
