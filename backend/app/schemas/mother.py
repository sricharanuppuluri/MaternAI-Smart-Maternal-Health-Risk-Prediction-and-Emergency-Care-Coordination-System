"""Mother profile and maternal risk tier schemas."""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class MaternalRiskLevel(str, Enum):
    """Documented maternal risk screening tiers."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MotherProfileCreate(BaseModel):
    """Payload to create maternal profile details."""
    date_of_birth: Optional[date] = None
    age_years: Optional[int] = Field(None, ge=12, le=65)
    gestational_age_weeks: Optional[int] = Field(None, ge=1, le=45)
    expected_due_date: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=50)


class MotherProfileUpdate(BaseModel):
    """Payload to update maternal profile details."""
    age_years: Optional[int] = Field(None, ge=12, le=65)
    gestational_age_weeks: Optional[int] = Field(None, ge=1, le=45)
    expected_due_date: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=50)


class MotherProfileResponse(BaseModel):
    """Mother profile response contract."""
    id: UUID
    user_id: UUID
    full_name: str
    date_of_birth: Optional[date] = None
    age_years: Optional[int] = None
    gestational_age_weeks: Optional[int] = None
    expected_due_date: Optional[date] = None
    assigned_asha_id: Optional[UUID] = None
    last_risk_level: Optional[MaternalRiskLevel] = None
    phone: Optional[str] = None
    created_at: datetime
