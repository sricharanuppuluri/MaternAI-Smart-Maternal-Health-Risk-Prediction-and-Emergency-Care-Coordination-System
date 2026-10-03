"""Longitudinal risk timeline schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from backend.app.schemas.mother import MaternalRiskLevel


class RiskTimelinePoint(BaseModel):
    """An individual assessment point on the mother's risk timeline."""
    timestamp: datetime
    risk_level: MaternalRiskLevel
    assessment_type: str  # "PREDICTION" or "SAFETY_EVENT"
    trigger_reason: Optional[str] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    hemoglobin: Optional[float] = None
    blood_sugar: Optional[float] = None


class RiskTimelineResponse(BaseModel):
    """Longitudinal risk timeline response (GET /api/v1/mothers/{id}/risk-timeline)."""
    mother_id: UUID
    current_risk_level: Optional[MaternalRiskLevel] = None
    assessments: List[RiskTimelinePoint]
