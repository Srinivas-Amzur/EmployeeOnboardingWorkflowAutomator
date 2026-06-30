"""
Middleware for the FastAPI application.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import time

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Log request and response."""
        start_time = time.time()

        # Log request
        logger.info(f"{request.method} {request.url.path}")

        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)")

        return response
