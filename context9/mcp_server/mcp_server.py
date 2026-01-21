from .client import GitHubClient
from loguru import logger
import sys
from .config import ConfigError
import argparse
from . import mcp_tools

github_client = None


def initialize_mcp_server(args: argparse.Namespace):
    """
    Initialize the MCP server with configuration.
    """
    global github_client

    try:
        # Initialize GitHub client
        github_client = GitHubClient(
            repos=args.repos,
            sync_interval=args.github_sync_interval,
            enable_github_webhook=args.enable_github_webhook,
        )
        logger.info("GitHub client initialized")

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}", exc_info=True)
        sys.exit(1)

    return github_client, mcp_tools.context9_mcp
