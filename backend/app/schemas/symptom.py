"""Symptom logging and reporting schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SymptomItem(BaseModel):
    """Individual reported symptom item."""
    symptom_code: str = Field(..., min_length=1, max_length=100, description="Standard symptom identifier (e.g. headache, bleeding, swelling_feet)")
    severity: int = Field(default=1, ge=1, le=5, description="Symptom severity scale (1: mild to 5: severe)")
    notes: Optional[str] = Field(None, max_length=1000, description="Optional observational notes")


class SymptomSubmission(BaseModel):
    """Payload to record maternal symptoms (POST /api/v1/symptoms)."""
    health_record_id: Optional[UUID] = Field(None, description="Optional associated health record")
    symptoms: List[SymptomItem] = Field(..., min_length=1, description="List of reported symptoms")


class SymptomResponse(BaseModel):
    """Symptom record response contract."""
    id: UUID
    mother_id: UUID
    health_record_id: Optional[UUID] = None
    symptom_code: str
    severity: int
    notes: Optional[str] = None
    recorded_at: datetime
    created_at: datetime
