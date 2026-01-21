from .mcp_auth import APIKeyMiddleware
from loguru import logger


class SelectiveAPIKeyMiddleware(APIKeyMiddleware):
    """Middleware that only applies API key check to MCP endpoints, not admin endpoints."""

    async def dispatch(self, request, call_next):
        # Skip API key check for admin endpoints (they use JWT) and MCP proxy (uses admin JWT)
        if request.url.path.startswith("/api/admin") or request.url.path.startswith(
            "/api/mcp-proxy"
        ):
            logger.info(
                f"Skipping API key check for admin/proxy endpoint: {request.url.path}"
            )
            return await call_next(request)
        # Apply API key check for MCP endpoints
        logger.info(f"Applying API key check for endpoint: {request.url.path}")
        return await super().dispatch(request, call_next)
