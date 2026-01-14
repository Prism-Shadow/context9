"""
Integration tests for MCP server.
"""

import pytest
from unittest.mock import Mock
from context9.server import read_doc
from context9.config import Config
from context9.github_client import GitHubClient


class TestServer:
    """Test cases for MCP server."""

    @pytest.fixture
    def mock_config(self, monkeypatch):
        """Create a mock configuration."""
        monkeypatch.setenv("GITHUB_OWNER", "test-owner")
        monkeypatch.setenv("GITHUB_REPO", "test-repo")
        monkeypatch.setenv("GITHUB_BRANCH", "main")
        return Config()

    @pytest.fixture
    def mock_github_client(self):
        """Create a mock GitHub client."""
        client = Mock(spec=GitHubClient)
        client.read_file = Mock(return_value="# Test Document\n\nContent here.")
        return client

    def test_read_doc_success(self, mock_config, mock_github_client, monkeypatch):
        """Test successful document reading."""
        # Mock the global github_client
        import context9.server as server_module

        server_module.github_client = mock_github_client

        result = read_doc("remotedoc://test.md")

        assert "# Test Document" in result
        mock_github_client.read_file.assert_called_once_with("test.md")

    def test_read_doc_invalid_url(self, mock_config, mock_github_client, monkeypatch):
        """Test reading document with invalid URL."""
        import context9.server as server_module

        server_module.github_client = mock_github_client

        with pytest.raises(ValueError, match="Invalid URL format"):
            read_doc("http://invalid-url")

    def test_read_doc_file_not_found(
        self, mock_config, mock_github_client, monkeypatch
    ):
        """Test reading non-existent document."""
        from remote_doc_mcp.github_client import GitHubFileNotFoundError

        import remote_doc_mcp.server as server_module

        mock_github_client.read_file.side_effect = GitHubFileNotFoundError(
            "File not found"
        )
        server_module.github_client = mock_github_client

        with pytest.raises(ValueError, match="Document not found"):
            read_doc("remotedoc://nonexistent.md")

    def test_read_doc_server_not_initialized(self, monkeypatch):
        """Test reading document when server is not initialized."""
        import context9.server as server_module

        server_module.github_client = None

        with pytest.raises(ValueError, match="Server not initialized"):
            read_doc("remotedoc://test.md")
