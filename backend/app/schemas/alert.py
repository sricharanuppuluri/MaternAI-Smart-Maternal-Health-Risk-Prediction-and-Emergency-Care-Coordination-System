"""Alert and ASHA workflow queue schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Documented alert severity tiers."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Documented ASHA case workflow states."""
    NEW = "NEW"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CONTACTED = "CONTACTED"
    VISIT_SCHEDULED = "VISIT_SCHEDULED"
    FOLLOW_UP_PENDING = "FOLLOW_UP_PENDING"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class AlertStatusUpdate(BaseModel):
    """Payload to update an alert status (PATCH /api/v1/alerts/{id}/status)."""
    status: AlertStatus
    notes: Optional[str] = Field(None, max_length=1000, description="ASHA action notes")


class AlertResponse(BaseModel):
    """Alert response contract."""
    id: UUID
    mother_id: UUID
    mother_name: Optional[str] = None
    asha_id: Optional[UUID] = None
    severity: AlertSeverity
    status: AlertStatus
    trigger_reason: str
    safety_event_id: Optional[UUID] = None
    prediction_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
