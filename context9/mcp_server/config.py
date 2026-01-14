"""
Configuration management for Context9.

This module handles loading and managing configuration from YAML files and environment variables.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from loguru import logger


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


class Config:
    """
    Configuration manager for Context9.
    """

    def __init__(self):
        """
        Initialize configuration.

        Args:
            config_path: Path to YAML configuration file (optional)
        """
        # Load environment variables from .env file
        load_dotenv()

        # Load configuration from file if provided
        self.config_data: Dict[str, Any] = {}

        # Load from environment variables (takes precedence)
        self._load_from_env()

        # Validate configuration
        self._validate()

    def _load_from_env(self):
        """Load configuration from environment variables."""
        # GitHub configuration
        github_config = self.config_data.get("github", {})

        if "GITHUB_OWNER" in os.environ:
            github_config["owner"] = os.environ["GITHUB_OWNER"]
        if "GITHUB_REPO" in os.environ:
            github_config["repo"] = os.environ["GITHUB_REPO"]
        if "GITHUB_BRANCH" in os.environ:
            github_config["branch"] = os.environ["GITHUB_BRANCH"]
        if "GITHUB_TOKEN" in os.environ:
            github_config["token"] = os.environ["GITHUB_TOKEN"]

        # Process token reference (e.g., "${GITHUB_TOKEN}")
        if "token" in github_config and isinstance(github_config["token"], str):
            token_value = github_config["token"]
            if token_value.startswith("${") and token_value.endswith("}"):
                env_var = token_value[2:-1]
                github_config["token"] = os.environ.get(env_var)

        self.config_data["github"] = github_config

        # Server configuration
        server_config = self.config_data.get("server", {})
        if "MCP_SERVER_NAME" in os.environ:
            server_config["name"] = os.environ["MCP_SERVER_NAME"]
        if "MCP_SERVER_DESCRIPTION" in os.environ:
            server_config["description"] = os.environ["MCP_SERVER_DESCRIPTION"]

        if "CTX9_API_KEY" in os.environ:
            server_config["api_key"] = os.environ["CTX9_API_KEY"]

        self.config_data["server"] = server_config

    def _validate(self):
        """Validate configuration."""
        github_config = self.config_data.get("github", {})

        # Check required fields
        if not github_config.get("owner"):
            raise ConfigError(
                "GitHub owner is required. Set GITHUB_OWNER environment variable or configure in YAML."
            )

        if not github_config.get("repo"):
            raise ConfigError(
                "GitHub repository is required. Set GITHUB_REPO environment variable or configure in YAML."
            )

        if not github_config.get("branch"):
            raise ConfigError(
                "GitHub branch is required. Set GITHUB_BRANCH environment variable or configure in YAML."
            )

        # Token is optional but recommended
        if not github_config.get("token"):
            logger.warning(
                "GitHub token not provided. API rate limits will be stricter."
            )

    @property
    def github_owner(self) -> str:
        """Get GitHub owner."""
        return self.config_data["github"]["owner"]

    @property
    def github_repo(self) -> str:
        """Get GitHub repository."""
        return self.config_data["github"]["repo"]

    @property
    def github_branch(self) -> str:
        """Get GitHub branch."""
        return self.config_data["github"].get("branch", "main")

    @property
    def github_token(self) -> Optional[str]:
        """Get GitHub token."""
        return self.config_data["github"].get("token")

    @property
    def server_name(self) -> str:
        """Get server name."""
        return self.config_data.get("server", {}).get("name", "Context9")

    @property
    def server_description(self) -> str:
        """Get server description."""
        return self.config_data.get("server", {}).get(
            "description", "MCP server for reading docs from GitHub"
        )

    @property
    def api_key(self) -> Optional[str]:
        """Get API key for authentication."""
        return self.config_data.get("server", {}).get("api_key")

    def get_github_config(self) -> Dict[str, Any]:
        """Get GitHub configuration as dictionary."""
        return {
            "owner": self.github_owner,
            "repo": self.github_repo,
            "branch": self.github_branch,
            "token": self.github_token,
        }
