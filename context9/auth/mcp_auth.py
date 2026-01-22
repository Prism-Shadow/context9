import hashlib
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response, JSONResponse
from starlette import status
from loguru import logger

from ..database import SessionLocal
from ..database.models import ApiKey
from dotenv import load_dotenv
import os

load_dotenv()

CTX9_API_KEY = os.getenv("CTX9_API_KEY")


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Supports API key validation from:
    - HTTP Header: Authorization header (Bearer token), case-insensitive
    """

    def __init__(self, app):
        """
        Initialize the API key middleware.

        Args:
            app: The ASGI application
        """
        super().__init__(app)

    async def dispatch(
        self, request: StarletteRequest, call_next: Callable
    ) -> Response:
        """
        Process the request and validate API key.

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

        if CTX9_API_KEY is None:
            # Verify API key against database (compare with stored key_hash)
            key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()
            db = SessionLocal()
            try:
                api_key_record = (
                    db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
                )
                if not api_key_record:
                    logger.warning(
                        f"Invalid API key provided in request to {request.url.path}"
                    )
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Invalid API key."},
                    )
            finally:
                db.close()
        else:
            if api_key_value != CTX9_API_KEY:
                logger.warning(
                    f"Invalid API key provided in request to {request.url.path}"
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Invalid API key."},
                )

        # API key exists in database, proceed with the request
        logger.debug(f"API key validated successfully for {request.url.path}")
        return await call_next(request)
