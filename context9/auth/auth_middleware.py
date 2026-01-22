from .mcp_auth import APIKeyMiddleware
from loguru import logger


class SelectiveAPIKeyMiddleware(APIKeyMiddleware):
    """
    Middleware that only applies API key check to MCP endpoints.

    Skips API key check for:
    - Admin endpoints (/api/admin/*) - use JWT authentication
    - MCP proxy endpoints (/api/mcp-proxy/*) - use admin JWT
    - GitHub webhook (/api/github) - uses webhook secret
    - Frontend static assets (/assets/*) - public resources
    - Frontend routes (all non-/api/* paths) - SPA routing
    - Static files (favicon.ico, etc.) - public resources
    """

    async def dispatch(self, request, call_next):
        path = request.url.path

        # Skip API key check for admin endpoints (they use JWT)
        if path.startswith("/api/admin"):
            logger.debug(f"Skipping API key check for admin endpoint: {path}")
            return await call_next(request)

        # Skip API key check for MCP proxy endpoints (uses admin JWT)
        if path.startswith("/api/mcp-proxy"):
            logger.debug(f"Skipping API key check for MCP proxy endpoint: {path}")
            return await call_next(request)

        # Skip API key check for GitHub webhook
        if path == "/api/github":
            logger.debug(f"Skipping API key check for GitHub webhook: {path}")
            return await call_next(request)

        # Skip API key check for frontend static assets
        if path.startswith("/assets/"):
            logger.debug(f"Skipping API key check for static asset: {path}")
            return await call_next(request)

        # Skip API key check for all non-API paths (frontend routes, static files, etc.)
        if not path.startswith("/api/"):
            logger.debug(f"Skipping API key check for non-API path: {path}")
            return await call_next(request)

        # Apply API key check only for MCP endpoints (/api/mcp/*)
        # All other /api/* paths should have been handled above
        logger.debug(f"Applying API key check for MCP endpoint: {path}")
        return await super().dispatch(request, call_next)
