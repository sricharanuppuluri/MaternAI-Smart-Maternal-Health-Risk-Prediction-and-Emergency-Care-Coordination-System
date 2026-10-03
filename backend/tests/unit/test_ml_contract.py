"""Unit tests for ML input schema contract."""

from backend.app.schemas.ml import MLRiskInput


def test_ml_risk_input_defaults():
    """Verify MLRiskInput defaults are all None/empty."""
    model_input = MLRiskInput()
    assert model_input.age_years is None
    assert model_input.hemoglobin is None
    assert model_input.systolic_bp is None
    assert model_input.diastolic_bp is None
    assert model_input.blood_sugar is None
    assert model_input.weight_kg is None
    assert model_input.pregnancy_week is None
    assert model_input.symptom_features == {}


def test_ml_risk_input_populated():
    """Verify MLRiskInput accepts valid numeric and symptom values."""
    payload = {
        "age_years": 26.5,
        "hemoglobin": 11.2,
        "systolic_bp": 120.0,
        "diastolic_bp": 80.0,
        "blood_sugar": 95.0,
        "weight_kg": 62.0,
        "pregnancy_week": 24,
        "symptom_features": {"headache": True, "swelling_feet": 1},
    }
    model_input = MLRiskInput(**payload)
    assert model_input.age_years == 26.5
    assert model_input.pregnancy_week == 24
    assert model_input.symptom_features["headache"] is True
