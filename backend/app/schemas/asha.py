"""ASHA worker profile and assignment schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class AshaProfileCreate(BaseModel):
    """Payload to create an ASHA worker profile."""
    worker_code: Optional[str] = Field(None, max_length=50)
    assigned_village: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)


class AshaProfileResponse(BaseModel):
    """ASHA worker profile response contract."""
    id: UUID
    user_id: UUID
    full_name: str
    worker_code: Optional[str] = None
    assigned_village: Optional[str] = None
    phone: Optional[str] = None
    active_cases_count: int = 0
    created_at: datetime


class AshaAssignmentResponse(BaseModel):
    """ASHA to mother assignment contract."""
    id: UUID
    asha_id: UUID
    mother_id: UUID
    assigned_at: datetime
    is_active: bool = True
