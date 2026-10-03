"""Health check and status response schemas."""

from pydantic import BaseModel


class HealthStatus(BaseModel):
    """Health status response payload."""
    status: str
    app: str
    version: str
    environment: str
