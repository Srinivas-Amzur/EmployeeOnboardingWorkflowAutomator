"""
Error handling and custom exceptions for the application.
"""

from fastapi import HTTPException, status
from pydantic import BaseModel
from typing import Any, Optional


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error_code: str
    error_message: str
    detail: Optional[str] = None
    request_id: Optional[str] = None


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        error_code: str,
        error_message: str,
        detail: Optional[str] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        """
        Initialize exception.

        Args:
            error_code: Machine-readable error code
            error_message: Human-readable error message
            detail: Additional error details
            status_code: HTTP status code
        """
        self.error_code = error_code
        self.error_message = error_message
        self.detail = detail
        self.status_code = status_code
        super().__init__(error_message)

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "error_code": self.error_code,
                "error_message": self.error_message,
                "detail": self.detail,
            },
        )


class ValidationException(AppException):
    """Exception for validation errors."""

    def __init__(self, message: str, detail: Optional[str] = None):
        """Initialize validation exception."""
        super().__init__(
            error_code="VALIDATION_ERROR",
            error_message="Validation failed",
            detail=detail or message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class AuthenticationException(AppException):
    """Exception for authentication failures."""

    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication exception."""
        super().__init__(
            error_code="AUTHENTICATION_ERROR",
            error_message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationException(AppException):
    """Exception for authorization failures."""

    def __init__(self, message: str = "Insufficient permissions"):
        """Initialize authorization exception."""
        super().__init__(
            error_code="AUTHORIZATION_ERROR",
            error_message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ResourceNotFoundException(AppException):
    """Exception for resource not found errors."""

    def __init__(self, resource_type: str, resource_id: str):
        """Initialize resource not found exception."""
        super().__init__(
            error_code="RESOURCE_NOT_FOUND",
            error_message=f"{resource_type} not found",
            detail=f"Could not find {resource_type} with ID: {resource_id}",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictException(AppException):
    """Exception for conflict errors (duplicate, etc.)."""

    def __init__(self, message: str, detail: Optional[str] = None):
        """Initialize conflict exception."""
        super().__init__(
            error_code="CONFLICT_ERROR",
            error_message=message,
            detail=detail,
            status_code=status.HTTP_409_CONFLICT,
        )


class DatabaseException(AppException):
    """Exception for database-related errors."""

    def __init__(self, message: str = "Database error occurred"):
        """Initialize database exception."""
        super().__init__(
            error_code="DATABASE_ERROR",
            error_message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ExternalServiceException(AppException):
    """Exception for external service failures."""

    def __init__(self, service_name: str, message: str = "External service error"):
        """Initialize external service exception."""
        super().__init__(
            error_code="EXTERNAL_SERVICE_ERROR",
            error_message=f"{service_name} error",
            detail=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class AIServiceException(AppException):
    """Exception for AI service failures."""

    def __init__(self, message: str = "AI service error occurred"):
        """Initialize AI service exception."""
        super().__init__(
            error_code="AI_SERVICE_ERROR",
            error_message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class RateLimitException(AppException):
    """Exception for rate limit violations."""

    def __init__(self, message: str = "Rate limit exceeded"):
        """Initialize rate limit exception."""
        super().__init__(
            error_code="RATE_LIMIT_EXCEEDED",
            error_message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


class BusinessLogicException(AppException):
    """Exception for business logic violations."""

    def __init__(self, message: str, detail: Optional[str] = None):
        """Initialize business logic exception."""
        super().__init__(
            error_code="BUSINESS_LOGIC_ERROR",
            error_message=message,
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


# Error code constants
ERROR_CODES = {
    "VALIDATION_ERROR": "Validation failed",
    "AUTHENTICATION_ERROR": "Authentication failed",
    "AUTHORIZATION_ERROR": "Insufficient permissions",
    "RESOURCE_NOT_FOUND": "Resource not found",
    "CONFLICT_ERROR": "Resource conflict",
    "DATABASE_ERROR": "Database error",
    "EXTERNAL_SERVICE_ERROR": "External service error",
    "AI_SERVICE_ERROR": "AI service error",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded",
    "BUSINESS_LOGIC_ERROR": "Business logic error",
    "INTERNAL_SERVER_ERROR": "Internal server error",
}
