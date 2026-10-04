"""Machine Learning request and response contracts.

Phase 0 establishes the documented contract without implementing
clinical interpretation or training pipelines.
"""

from typing import Dict, Union, Optional
from pydantic import BaseModel, Field


class MLRiskInput(BaseModel):
    """Documented feature contract for future ML risk screening models.
    
    All vital and measurement fields are nullable to handle real-world screening scenarios.
    """
    age_years: Optional[float] = None
    hemoglobin: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    blood_sugar: Optional[float] = None
    weight_kg: Optional[float] = None
    pregnancy_week: Optional[int] = None
    body_temperature: Optional[float] = None
    heart_rate: Optional[float] = None
    symptom_features: Dict[str, Union[int, float, bool]] = Field(default_factory=dict)
