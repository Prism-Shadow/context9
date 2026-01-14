from .github_client import GitHubClient
from loguru import logger
import sys
from .config import ConfigError
import argparse
import os
from dotenv import load_dotenv

github_client = None
api_key = None


def initialize_mcp_server(args: argparse.Namespace):
    """
    Initialize the MCP server with configuration.
    """
    global github_client, api_key
    load_dotenv()
    github_token = None
    if "GITHUB_TOKEN" in os.environ:
        github_token = os.environ["GITHUB_TOKEN"]

    if "CTX9_API_KEY" in os.environ:
        api_key = os.environ["CTX9_API_KEY"]

    # config: Optional[Config] = Config()

    try:
        # Initialize GitHub client
        github_client = GitHubClient(
            repos=args.repos,
            token=github_token,
            sync_interval=args.github_sync_interval,
            enable_github_webhook=args.enable_github_webhook,
        )
        logger.info("GitHub client initialized")
        # Store API key for authentication
        api_key = os.environ.get("CTX9_API_KEY")
        if not api_key:
            logger.error("API key not found in environment variables")
            raise ValueError("API key not found in environment variables")
        logger.info(f"API key: {api_key}")

    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}", exc_info=True)
        sys.exit(1)

    return api_key, github_client
