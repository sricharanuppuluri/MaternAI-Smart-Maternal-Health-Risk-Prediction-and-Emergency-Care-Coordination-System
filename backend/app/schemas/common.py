"""Common API response schemas, error envelopes, and pagination models.

Conforms to standard JSON error contract and pagination conventions.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiErrorDetail(BaseModel):
    """Standardized API error detail."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ApiErrorResponse(BaseModel):
    """Standardized top-level API error envelope.
    
    Format:
    {
      "error": {
        "code": "...",
        "message": "...",
        "details": {}
      }
    }
    """
    error: ApiErrorDetail


class PaginationParams(BaseModel):
    """Standard query parameters for paginated list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response wrapper."""
    items: List[T]
    total: int
    page: int
    size: int
    total_pages: int
