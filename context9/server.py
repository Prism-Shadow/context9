"""
MCP Server for Context9.

This module implements the main MCP server using FastMCP.
"""

import argparse

from loguru import logger

from .mcp_server import initialize_mcp_server
import uvicorn
import yaml
import os
from .auth import APIKeyMiddleware


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Context9 MCP Server"
            "This server is used to read documents from GitHub repositories."
        )
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--enable_github_webhook", action="store_true", help="Enable GitHub webhook"
    )
    group.add_argument(
        "--github_sync_interval",
        type=int,
        default=None,
        help="GitHub sync interval in seconds",
    )
    parser.add_argument(
        "--config_file",
        type=str,
        default=None,
        help="Config file path",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8011,
        help="Port to run the server on",
    )

    return parser.parse_args()


def read_config(config_file_path: str):
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f"Config file not found: {config_file_path}")

    try:
        with open(config_file_path, "r") as file:
            config = yaml.safe_load(file)

        if not config:
            raise Exception("Config file is empty")

        if not config.get("repos"):
            raise Exception("Repos is not set in config file")

        for repo in config["repos"]:
            if not repo.get("root_spec_path"):
                repo["root_spec_path"] = "spec.md"

    except Exception as e:
        raise Exception(f"Failed to read config file: {e}")

    return config


def main():
    """Main entry point for the MCP server."""

    args = parse_args()
    yaml_config = read_config(args.config_file)
    args.repos = yaml_config["repos"]
    logger.info(f"Arguments: {args}")
    if args.enable_github_webhook:
        logger.info("GitHub webhook is enabled")
    else:
        logger.info("GitHub webhook is disabled")
    # Initialize server
    logger.info("Initializing MCP server...")
    api_key, github_client, context9_mcp = initialize_mcp_server(args)
    logger.info("MCP server initialized")

    # Create the MCP server as a Starlette app
    app = context9_mcp.http_app(path="/api/mcp/")

    # Setup GitHub webhook route
    app.add_route("/api/github", github_client.handle_github_webhook, methods=["POST"])
    logger.info(
        f"GitHub webhook endpoint available at http://0.0.0.0:{args.port}/api/github"
    )

    # Add API key authentication middleware
    app.add_middleware(APIKeyMiddleware, api_key=api_key)

    logger.info(f"MCP server running on http://0.0.0.0:{args.port}/api/mcp/")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
