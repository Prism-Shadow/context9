"""
MCP Server for Context9.

This module implements the main MCP server using FastMCP.
"""

import argparse

from typing import Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response, JSONResponse
from starlette import status

from loguru import logger

from .mcp_server import initialize_mcp_server, context9_mcp
import uvicorn
import yaml
import os


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Supports API key validation from:
    - HTTP Header: Authorization header (Bearer token), case-insensitive
    """

    def __init__(self, app, api_key: Optional[str] = None):
        """
        Initialize the API key middleware.

        Args:
            app: The ASGI application
            api_key: The API key to validate against. If None, authentication is disabled.
        """
        super().__init__(app)
        # Store reference to module to get latest api_key value
        self.api_key = api_key
        logger.info(
            f"API key middleware initialized with provided api_key: {api_key[:10] if api_key and len(api_key) > 10 else (api_key if api_key else 'None')}"
        )

    async def dispatch(
        self, request: StarletteRequest, call_next: Callable
    ) -> Response:
        """
        Process the request and validate API key if configured.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the next handler or an error response
        """
        # Log request headers for debugging
        logger.info(f"Request headers: {dict(request.headers)}")
        # Check for Authorization header (case-insensitive)
        auth_header_key = None
        for key in request.headers.keys():
            if key.lower() == "authorization":
                auth_header_key = key
                break
        logger.info(f"Authorization header present: {auth_header_key is not None}")
        if auth_header_key:
            logger.info(
                f"Authorization header value: {request.headers[auth_header_key][:50]}..."
            )  # Log first 50 chars for security

        # Skip API key authentication for GitHub webhook endpoint
        # GitHub webhooks use their own signature verification (X-Hub-Signature-256)
        if request.url.path == "/api/github":
            return await call_next(request)

        # If no API key is configured, reject the service
        if not self.api_key:
            logger.warning("API key is not configured, rejecting service")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "Service is not available. API key is not configured."
                },
            )

        # Log client IP and target address
        client_ip = request.client.host if request.client else "unknown"
        client_port = request.client.port if request.client else "unknown"
        target_host = request.url.hostname or "unknown"
        target_port = request.url.port or (443 if request.url.scheme == "https" else 80)
        logger.info(
            f"Request from {client_ip}:{client_port} to {target_host}:{target_port}"
        )

        # Try to get API key from Authorization header (case-insensitive)
        api_key_value = None

        # Find Authorization header (case-insensitive)
        auth_header_key = None
        for key in request.headers.keys():
            if key.lower() == "authorization":
                auth_header_key = key
                break

        # Check Authorization header (Bearer token, case-insensitive)
        if auth_header_key:
            auth_header = request.headers[auth_header_key]
            # Check for Bearer prefix (case-insensitive)
            if auth_header.lower().startswith("bearer "):
                api_key_value = auth_header[
                    7:
                ]  # Remove "Bearer " prefix (case-insensitive)
            else:
                # If no Bearer prefix, reject the request
                logger.warning(
                    f"Authorization header does not use Bearer token format in request to {request.url.path}"
                )
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "detail": "Authorization header must use Bearer token format: 'Bearer <token>'"
                    },
                )

        # Validate API key
        if not api_key_value:
            logger.warning(f"API key missing in request to {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "API key is required. Provide it via Authorization header with Bearer token format: 'Authorization: Bearer <token>'"
                },
            )

        if api_key_value != self.api_key:
            logger.warning(f"Invalid API key provided in request to {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid API key."},
            )

        # API key is valid, proceed with the request
        logger.info(f"API key validated successfully for {request.url.path}")
        return await call_next(request)


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
    api_key, github_client = initialize_mcp_server(args)
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
