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
from .auth import SelectiveAPIKeyMiddleware
from .database.init_db import initialize_database
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from starlette.routing import Mount
from .api import admin, api_keys, mcp_proxy, repositories
from pathlib import Path

from dotenv import load_dotenv


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
    if args.config_file:
        yaml_config = read_config(args.config_file)
        args.repos = yaml_config["repos"]
    else:
        args.repos = None

    load_dotenv()
    args.port = os.getenv("PORT", 8011)
    logger.info(f"Arguments: {args}")

    if args.enable_github_webhook:
        logger.info("GitHub webhook is enabled")
    else:
        logger.info("GitHub webhook is disabled")

    # Initialize database
    logger.info("Initializing database...")
    try:
        initialize_database()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error("This is a critical error. Admin login will not work.")
        logger.error("Please check:")
        logger.error("  1. Database file permissions")
        logger.error("  2. Database file is not corrupted")
        logger.error(
            "  3. CONTEXT9_ADMIN_USERNAME and CONTEXT9_ADMIN_PASSWORD environment variables (if set)"
        )
        logger.error("You can try running: python -m context9.database.init_db")
        # Still continue - user might want to fix it manually
        logger.warning("Server will start, but admin functionality may not work.")

    logger.info("Initializing MCP server...")
    github_client, context9_mcp = initialize_mcp_server(args)
    logger.info("MCP server initialized")

    # Create the MCP server as a Starlette app.
    mcp_app = context9_mcp.http_app(path="/")

    # Create FastAPI app for admin panel
    admin_app = FastAPI(title="Context9 Admin API", version="0.1.0")

    # Add CORS middleware to support cross-origin requests
    admin_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, replace with specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup admin API routes (must be before static files)
    admin_app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
    admin_app.include_router(
        api_keys.router, prefix="/api/admin/api-keys", tags=["api-keys"]
    )
    admin_app.include_router(
        repositories.router, prefix="/api/admin/repositories", tags=["repositories"]
    )
    admin_app.include_router(
        mcp_proxy.router, prefix="/api/mcp-proxy", tags=["mcp-proxy"]
    )

    # Mount frontend static files if they exist (production mode)
    # This must be after API routes to ensure API routes take precedence
    gui_dist_path = Path(__file__).parent.parent.parent / "gui" / "dist"
    if gui_dist_path.exists() and (gui_dist_path / "index.html").exists():
        logger.info(f"Serving frontend from {gui_dist_path}")
        # Mount static files, but exclude /api routes
        admin_app.mount(
            "/", StaticFiles(directory=str(gui_dist_path), html=True), name="static"
        )
    else:
        logger.info(
            "Frontend build not found, serving API only. Run 'npm run build' in gui/ to build frontend."
        )

    # Create main app that combines both.
    app = Starlette(
        routes=[
            Mount("/api/mcp", app=mcp_app),
            Mount("", app=admin_app),
        ],
        lifespan=mcp_app.lifespan,
    )

    # Setup GitHub webhook route
    app.add_route("/api/github", github_client.handle_github_webhook, methods=["POST"])
    logger.info(
        f"GitHub webhook endpoint available at http://0.0.0.0:{args.port}/api/github"
    )

    # Add selective API key authentication middleware
    app.add_middleware(SelectiveAPIKeyMiddleware)

    logger.info(f"MCP server running on http://0.0.0.0:{args.port}/api/mcp/")
    logger.info(f"Admin API running on http://0.0.0.0:{args.port}/api/admin/")

    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
