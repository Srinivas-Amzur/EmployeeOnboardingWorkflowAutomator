"""
Error handling middleware for the application.
"""

import logging
import time
import uuid
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..core.logging import clear_request_context, set_request_context
from ..core.security import decode_token
from ..core.exceptions import AppException, ErrorResponse

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors across the application."""

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        """
        Process request and handle errors.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or str(uuid.uuid4())
        correlation_id = (
            getattr(request.state, "correlation_id", None)
            or request.headers.get("x-correlation-id")
            or request_id
        )
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        try:
            response = await call_next(request)
            return response

        except AppException as e:
            # Application-specific exception
            logger.warning(
                f"[{request_id}] Application error: {e.error_code} - {e.error_message}",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )

            error_response = ErrorResponse(
                error_code=e.error_code,
                error_message=e.error_message,
                detail=e.detail,
                request_id=request_id,
            )

            return JSONResponse(
                status_code=e.status_code,
                content=error_response.model_dump(exclude_none=True),
            )

        except ValueError as e:
            # Validation error
            logger.warning(
                f"[{request_id}] Validation error: {str(e)}",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )

            error_response = ErrorResponse(
                error_code="VALIDATION_ERROR",
                error_message="Validation failed",
                detail=str(e),
                request_id=request_id,
            )

            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response.model_dump(exclude_none=True),
            )

        except Exception as e:
            # Unexpected error
            logger.exception(
                f"[{request_id}] Unexpected error: {type(e).__name__}",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )

            error_response = ErrorResponse(
                error_code="INTERNAL_SERVER_ERROR",
                error_message="An unexpected error occurred",
                detail="Please contact support with the request ID",
                request_id=request_id,
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump(exclude_none=True),
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        """
        Log request and response.

        Args:
            request: HTTP request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id") or str(uuid.uuid4())
        correlation_id = (
            getattr(request.state, "correlation_id", None)
            or request.headers.get("x-correlation-id")
            or request_id
        )

        user_id = "anonymous"
        access_token = request.cookies.get("access_token")
        if access_token:
            token_data = decode_token(access_token)
            if token_data:
                user_id = token_data.sub

        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        request.state.user_id = user_id
        set_request_context(request_id=request_id, correlation_id=correlation_id, user_id=user_id)

        started = time.perf_counter()

        logger.info(
            "HTTP REQUEST STARTED",
            extra={
                "request_id": request_id,
                "correlation_id": correlation_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        try:
            response = await call_next(request)

            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id

            logger.info(
                "HTTP RESPONSE",
                extra={
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "user_id": user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "client_ip": request.client.host if request.client else "unknown",
                },
            )

            return response
        finally:
            clear_request_context()
