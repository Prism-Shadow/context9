from typing import Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response, JSONResponse
from starlette import status
from loguru import logger


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

        # Only validate API key for /api/mcp endpoint
        # All other URLs are allowed without authentication
        if request.url.path != "/api/mcp":
            logger.info(f"Skipping API key validation for {request.url.path}")
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
