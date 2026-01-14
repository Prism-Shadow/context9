"""
Tests for configuration module.
"""

import pytest
from context9.config import Config, ConfigError


class TestConfig:
    """Test cases for configuration."""

    def test_config_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("GITHUB_OWNER", "test-owner")
        monkeypatch.setenv("GITHUB_REPO", "test-repo")
        monkeypatch.setenv("GITHUB_BRANCH", "develop")
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")

        config = Config()

        assert config.github_owner == "test-owner"
        assert config.github_repo == "test-repo"
        assert config.github_branch == "develop"
        assert config.github_token == "test-token"

    def test_config_missing_owner(self):
        """Test that missing required fields raise error."""
        with pytest.raises(ConfigError, match="owner is required"):
            Config()
