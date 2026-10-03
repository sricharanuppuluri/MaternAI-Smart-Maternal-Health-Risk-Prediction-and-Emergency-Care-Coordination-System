"""Standard API exceptions and error codes.

Conforms to standard error format:
{
  "error": {
    "code": "...",
    "message": "...",
    "details": {}
  }
}
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class AppError(HTTPException):
    """Base application exception mapping to standard API error contract."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or {},
                }
            },
        )
        self.code = code
        self.message = message
        self.details = details or {}


class UnauthorizedError(AppError):
    """401 Unauthorized: missing or invalid authentication token."""

    def __init__(self, message: str = "Authentication required or token invalid", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            message=message,
            details=details,
        )


class ForbiddenError(AppError):
    """403 Forbidden: authenticated user lacks permission for the resource."""

    def __init__(self, message: str = "Access forbidden for current user or role", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
            details=details,
        )


class NotFoundError(AppError):
    """404 Not Found."""

    def __init__(self, message: str = "Requested resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=message,
            details=details,
        )


class ValidationError(AppError):
    """422 / 400 Validation Error."""

    def __init__(self, message: str = "Validation failed for supplied input", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )
