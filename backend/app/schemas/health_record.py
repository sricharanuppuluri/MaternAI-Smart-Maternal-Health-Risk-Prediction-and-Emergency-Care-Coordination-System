"""Health record schemas for vital signs and maternal measurements."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class HealthRecordCreate(BaseModel):
    """Payload to record new maternal health measurements (POST /api/v1/health-records)."""
    pregnancy_week: Optional[int] = Field(None, ge=1, le=45, description="Gestational week")
    systolic_bp: Optional[float] = Field(None, ge=50.0, le=250.0, description="Systolic blood pressure (mmHg)")
    diastolic_bp: Optional[float] = Field(None, ge=30.0, le=160.0, description="Diastolic blood pressure (mmHg)")
    blood_sugar: Optional[float] = Field(None, ge=20.0, le=500.0, description="Blood glucose (mg/dL)")
    hemoglobin: Optional[float] = Field(None, ge=2.0, le=25.0, description="Hemoglobin (g/dL)")
    weight_kg: Optional[float] = Field(None, ge=20.0, le=200.0, description="Weight (kg)")
    body_temperature: Optional[float] = Field(None, ge=30.0, le=45.0, description="Body temperature (°C)")
    heart_rate: Optional[float] = Field(None, ge=30.0, le=220.0, description="Heart rate (bpm)")
    recorded_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Timestamp of measurement")


class HealthRecordResponse(BaseModel):
    """Health record response contract."""
    id: UUID
    mother_id: UUID
    pregnancy_week: Optional[int] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    blood_sugar: Optional[float] = None
    hemoglobin: Optional[float] = None
    weight_kg: Optional[float] = None
    body_temperature: Optional[float] = None
    heart_rate: Optional[float] = None
    recorded_by: Optional[UUID] = None
    recorded_at: datetime
    created_at: datetime
