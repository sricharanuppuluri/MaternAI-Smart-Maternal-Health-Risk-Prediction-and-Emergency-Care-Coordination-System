"""ASHA follow-up task and tracking schemas."""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class FollowUpStatus(str, Enum):
    """Documented follow-up tracking status."""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class FollowUpCreate(BaseModel):
    """Payload to schedule an ASHA follow-up (POST /api/v1/followups)."""
    mother_id: UUID
    alert_id: Optional[UUID] = None
    visit_id: Optional[UUID] = None
    due_date: date
    notes: Optional[str] = Field(None, max_length=1000)


class FollowUpResponse(BaseModel):
    """Follow-up response contract."""
    id: UUID
    mother_id: UUID
    asha_id: UUID
    alert_id: Optional[UUID] = None
    visit_id: Optional[UUID] = None
    due_date: date
    status: FollowUpStatus
    notes: Optional[str] = None
    created_at: datetime
