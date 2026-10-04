"""Machine Learning request and response contracts.

Phase 5 establishes explicit vital unit declarations and feature schemas
for the trained maternal risk prediction pipeline.
"""

from enum import Enum
from typing import Dict, Optional, Union
from pydantic import BaseModel, Field


class BloodSugarUnit(str, Enum):
    """Explicit blood sugar measurement unit."""
    MG_DL = "mg/dL"
    MMOL_L = "mmol/L"


class TemperatureUnit(str, Enum):
    """Explicit body temperature measurement unit."""
    CELSIUS = "C"
    FAHRENHEIT = "F"


class MLRiskInput(BaseModel):
    """Documented feature contract for ML risk screening models.

    All vital and measurement fields are nullable to handle real-world screening scenarios.
    Explicit unit indicators prevent silent clinical unit confusion.
    """
    age_years: Optional[float] = None
    hemoglobin: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    blood_sugar: Optional[float] = None
    blood_sugar_unit: Optional[BloodSugarUnit] = Field(
        default=BloodSugarUnit.MG_DL,
        description="Measurement unit for blood_sugar: 'mg/dL' (system standard) or 'mmol/L' (UCI model canonical)",
    )
    weight_kg: Optional[float] = None
    pregnancy_week: Optional[int] = None
    body_temperature: Optional[float] = None
    temperature_unit: Optional[TemperatureUnit] = Field(
        default=TemperatureUnit.CELSIUS,
        description="Measurement unit for body_temperature: 'C' (system standard) or 'F' (UCI model canonical)",
    )
    heart_rate: Optional[float] = None
    symptom_features: Dict[str, Union[int, float, bool]] = Field(default_factory=dict)
