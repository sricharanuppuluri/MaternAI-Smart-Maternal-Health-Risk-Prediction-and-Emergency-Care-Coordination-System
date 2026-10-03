"""Machine Learning prediction request and response contracts."""

from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field

from backend.app.schemas.ml import MLRiskInput
from backend.app.schemas.mother import MaternalRiskLevel


class ContributingFactor(BaseModel):
    """Documented explainability factor indicating feature influence on screening."""
    feature: str = Field(..., description="Feature name")
    direction: str = Field(..., description="Direction of contribution: INCREASES_RISK or DECREASES_RISK")
    value: Union[float, int, str, bool, None] = Field(None, description="Observed value of the feature")


class PredictionRequest(BaseModel):
    """Payload to trigger risk assessment (POST /api/v1/predictions)."""
    health_record_id: Optional[UUID] = Field(None, description="Existing health record ID to evaluate")
    features: Optional[MLRiskInput] = Field(None, description="Direct feature input payload if health record is not yet persisted")


class PredictionResponse(BaseModel):
    """Prediction response contract.
    
    Note: model_score is an internal screening metric, NOT a calibrated medical probability.
    """
    id: UUID
    mother_id: UUID
    health_record_id: Optional[UUID] = None
    risk_level: MaternalRiskLevel
    model_score: Optional[float] = None
    model_version: str
    feature_schema_version: str
    contributing_factors: List[ContributingFactor] = Field(default_factory=list)
    created_at: datetime
