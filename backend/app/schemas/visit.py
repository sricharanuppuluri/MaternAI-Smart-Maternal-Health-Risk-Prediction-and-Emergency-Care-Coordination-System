"""ASHA in-person and home visit schemas."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class VisitStatus(str, Enum):
    """Documented visit workflow status."""
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"


class VisitCreate(BaseModel):
    """Payload to schedule or record an ASHA visit (POST /api/v1/visits)."""
    mother_id: UUID
    alert_id: Optional[UUID] = None
    visit_date: datetime
    notes: Optional[str] = Field(None, max_length=2000)
    findings: Dict[str, Any] = Field(default_factory=dict)


class VisitResponse(BaseModel):
    """Visit response contract."""
    id: UUID
    mother_id: UUID
    asha_id: UUID
    alert_id: Optional[UUID] = None
    visit_date: datetime
    status: VisitStatus
    notes: Optional[str] = None
    findings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
