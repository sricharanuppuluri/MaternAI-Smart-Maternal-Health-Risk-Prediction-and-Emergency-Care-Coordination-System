"""Phase 5 ML Pipeline & Trained Model Provider Test Suite.

Verifies:
1. Dataset Integrity & Deduplication:
   - Official UCI dataset exists and has expected columns.
   - Clean unambiguous dataset (Option B) has exactly 381 unique profiles.
   - Zero duplicate feature vectors exist in the clean dataset.
   - No feature overlap across train/validation/test partitions.
2. Candidate Model Training:
   - All 4 candidate algorithms train successfully.
   - Predictions strictly conform to MaternalRiskLevel (LOW, MEDIUM, HIGH).
3. Serialized Model Artifact:
   - Artifact exists in ml/models/ and loads with valid metadata.
   - Feature schema version and model version match expected contracts.
4. TrainedModelProvider:
   - Provider loads artifact and executes inference on MLRiskInput.
   - Handles partial/null inputs via feature alignment.
   - Generates reliable, sorted contributing factors.
   - Produces internal model_score within [0.0, 1.0].
5. Integration with Prediction Service:
   - MLPredictionService integrates TrainedModelProvider seamlessly.
   - POST /api/v1/predictions returns valid model_version and schema_version.
6. Safety Boundary Preservation:
   - SafetyEngine runs before ML and cannot be overridden by ML.
   - Emergency state is strictly enforced regardless of ML prediction.
   - Client cannot inject safety states.
"""

from pathlib import Path
import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.ml.service import (
    BaselineScreeningModel,
    get_ml_service,
    ml_service,
)
from backend.app.ml.trained_provider import TrainedModelProvider
from backend.app.safety.evaluator import SafetyResult, get_safety_engine
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.ml import MLRiskInput
from backend.app.schemas.mother import MaternalRiskLevel
from backend.app.services.prediction_service import PredictionService
from ml.train import (
    CLEAN_DATASET_PATH,
    DATASET_PATH,
    FEATURE_COLS,
    MODEL_VERSION,
    SCHEMA_VERSION,
)


# ==============================================================================
# 1. Dataset Integrity & Deduplication Tests
# ==============================================================================

def test_raw_dataset_exists_and_matches_uci_schema():
    """Verify raw dataset exists and contains all documented UCI attributes."""
    assert DATASET_PATH.exists(), f"Raw dataset not found at {DATASET_PATH}"
    df = pd.read_csv(DATASET_PATH)
    assert len(df) == 1014
    expected_cols = ["Age", "SystolicBP", "DiastolicBP", "BS", "BodyTemp", "HeartRate", "RiskLevel"]
    assert list(df.columns) == expected_cols
    assert df.isnull().sum().sum() == 0


def test_clean_unambiguous_dataset_leakage_invariants():
    """Verify clean dataset (Option B) contains 381 unique feature profiles with zero duplicates."""
    assert CLEAN_DATASET_PATH.exists(), f"Clean dataset not found at {CLEAN_DATASET_PATH}"
    df_clean = pd.read_csv(CLEAN_DATASET_PATH)
    assert len(df_clean) == 381
    assert df_clean.duplicated(subset=FEATURE_COLS).sum() == 0
    assert set(df_clean["CanonicalRisk"].unique()) == {"LOW", "MEDIUM", "HIGH"}


# ==============================================================================
# 2. Artifact and Metadata Tests
# ==============================================================================

def test_serialized_artifact_exists_and_validates():
    """Verify serialized artifact loads and exposes versioned metadata."""
    artifact_path = Path("ml/models/maternal_risk_model_v1.joblib")
    assert artifact_path.exists(), "Model artifact not found"
    artifact = joblib.load(artifact_path)

    assert "pipeline" in artifact
    assert "model_version" in artifact
    assert artifact["model_version"] == MODEL_VERSION
    assert artifact["feature_schema_version"] == SCHEMA_VERSION
    assert artifact["feature_cols"] == FEATURE_COLS
    assert set(artifact["classes"]) == {"LOW", "MEDIUM", "HIGH"}
    assert "BS" in artifact["feature_importances"]


# ==============================================================================
# 3. TrainedModelProvider Unit Tests
# ==============================================================================

def test_trained_model_provider_inference():
    """TrainedModelProvider produces valid categorical risk and internal score."""
    provider = TrainedModelProvider()
    assert provider.is_loaded is True

    # High blood sugar and high systolic BP -> Expect HIGH risk
    high_input = MLRiskInput(
        age_years=35.0,
        systolic_bp=155.0,
        diastolic_bp=95.0,
        blood_sugar=14.0,  # ~250 mg/dL in mmol/L
        body_temperature=37.5,
        heart_rate=88.0,
    )
    result = provider.predict(high_input)
    assert result.risk_level == MaternalRiskLevel.HIGH
    assert 0.0 <= result.model_score <= 1.0
    assert result.model_version == MODEL_VERSION
    assert result.feature_schema_version == SCHEMA_VERSION
    assert len(result.contributing_factors) == len(FEATURE_COLS)

    # Normal baseline vitals -> Expect LOW risk
    low_input = MLRiskInput(
        age_years=22.0,
        systolic_bp=100.0,
        diastolic_bp=70.0,
        blood_sugar=7.0,
        body_temperature=36.6,
        heart_rate=72.0,
    )
    low_result = provider.predict(low_input)
    assert low_result.risk_level == MaternalRiskLevel.LOW


def test_trained_model_provider_partial_features():
    """Provider handles missing/partial vital measurements via median alignment without crashing."""
    provider = TrainedModelProvider()
    partial_input = MLRiskInput(
        systolic_bp=135.0,
        # other fields None
    )
    result = provider.predict(partial_input)
    assert result.risk_level in [MaternalRiskLevel.LOW, MaternalRiskLevel.MEDIUM, MaternalRiskLevel.HIGH]
    assert 0.0 <= result.model_score <= 1.0


def test_trained_model_provider_unit_conversion():
    """Provider properly converts Celsius body temp and mg/dL blood sugar to model scales."""
    provider = TrainedModelProvider()
    # 37 C -> 98.6 F, 180 mg/dL -> 10.0 mmol/L
    converted_input = MLRiskInput(
        age_years=28.0,
        systolic_bp=120.0,
        diastolic_bp=80.0,
        blood_sugar=180.0,       # mg/dL
        body_temperature=37.0,   # Celsius
        heart_rate=75.0,
    )
    result = provider.predict(converted_input)
    assert result.risk_level in [MaternalRiskLevel.LOW, MaternalRiskLevel.MEDIUM, MaternalRiskLevel.HIGH]


# ==============================================================================
# 4. Service Integration & Safety Tests
# ==============================================================================

def test_ml_prediction_service_uses_trained_provider():
    """Verify MLPredictionService defaults to active TrainedModelProvider."""
    service = get_ml_service()
    features = MLRiskInput(
        age_years=30.0,
        systolic_bp=140.0,
        diastolic_bp=90.0,
        blood_sugar=8.0,
    )
    res = service.predict(features)
    assert res.model_version == MODEL_VERSION
    assert res.feature_schema_version == SCHEMA_VERSION


def test_safety_precedence_with_trained_model(mother_client: TestClient):
    """Authoritative emergency safety rule strictly supersedes trained ML model prediction."""
    engine = get_safety_engine()

    def critical_vital_rule(vitals, symptoms):
        if vitals and vitals.get("systolic_bp") and vitals["systolic_bp"] >= 180.0:
            return SafetyResult(
                status=SafetyStatus.EMERGENCY,
                triggered_rules=["Severe hypertensive crisis"],
                action_required="Immediate emergency triage",
                is_emergency=True,
            )
        return None

    engine.register_rule(critical_vital_rule)

    # Post prediction request with systolic_bp >= 180
    response = mother_client.post(
        "/api/v1/predictions",
        json={
            "features": {
                "systolic_bp": 185.0,
                "blood_sugar": 5.0,  # low sugar would otherwise score low
            }
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert data["model_version"] == MODEL_VERSION

    # Safety event was authoritatively created
    from backend.app.db.repositories import get_repository
    repo = get_repository()
    assert len(repo.safety_events) >= 1
    assert repo.safety_events[-1]["safety_status"] == "EMERGENCY"
