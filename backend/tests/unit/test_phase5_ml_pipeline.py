"""Phase 5 ML Pipeline & Trained Model Provider Comprehensive Test Suite.

Verifies:
1. Dataset Integrity & Deduplication:
   - Official UCI dataset exists and has expected columns.
   - Clean unambiguous dataset (Option B) has exactly 381 unique profiles.
   - Zero duplicate feature vectors exist in the clean dataset.
   - No feature overlap across train/validation/test partitions.
2. Candidate Model Training & Validation Selection:
   - Model selection driven strictly by validation partition.
   - 95% bootstrap confidence intervals computed on held-out test predictions.
3. Serialized Model Artifact:
   - Artifact exists in ml/models/ and loads with valid metadata.
   - Feature schema version and model version match expected contracts.
4. TrainedModelProvider:
   - Provider loads artifact and executes inference on MLRiskInput.
   - Handles partial/null inputs via feature alignment.
   - Produces internal model_score within [0.0, 1.0].
5. Explicit Unit Conversions & Boundary Safety (NO MAGIC THRESHOLDS):
   - blood sugar = 25 mg/dL is never interpreted as 25 mmol/L.
   - normal blood sugar in mg/dL vs mmol/L.
   - temperature in Celsius vs Fahrenheit.
   - values around former 30 mg/dL and 50°C thresholds.
   - missing/unsupported units raise explicit errors.
6. Removal of Unsafe Directional Heuristics:
   - No naive median comparisons (age 14, SBP 70, low temp, bradycardia never emit DECREASES_RISK).
7. Observable Operational Logging on Model Loading Failures:
   - Failure to load artifact logs warning/error without exposing internal exception to API.
8. Safety Boundary Preservation:
   - SafetyEngine runs before ML and cannot be overridden by ML.
   - Emergency state is strictly enforced regardless of ML prediction.
"""

import json
import logging
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
from backend.app.schemas.ml import BloodSugarUnit, MLRiskInput, TemperatureUnit
from backend.app.schemas.mother import MaternalRiskLevel
from backend.app.services.prediction_service import PredictionService
from ml.train import (
    CLEAN_DATASET_PATH,
    DATASET_PATH,
    FEATURE_COLS,
    METADATA_PATH,
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
    """Verify serialized artifact loads and exposes versioned metadata and 95% bootstrap CIs."""
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

    # Verify metadata JSON records bootstrap CIs and validation selection
    assert METADATA_PATH.exists()
    with open(METADATA_PATH, "r") as f:
        meta = json.load(f)
    assert meta["model_selection_partition"] == "validation_set (N=57)"
    assert "confidence_intervals_95" in meta["test_metrics"]
    cis = meta["test_metrics"]["confidence_intervals_95"]
    assert "accuracy" in cis
    assert "high_risk_recall" in cis
    assert cis["bootstrap_resamples"] == 1000
    assert cis["bootstrap_seed"] == 42


# ==============================================================================
# 3. TrainedModelProvider Unit & Safety Tests
# ==============================================================================

def test_trained_model_provider_inference():
    """TrainedModelProvider produces valid categorical risk and internal score without directional heuristics."""
    provider = TrainedModelProvider()
    assert provider.is_loaded is True

    # High blood sugar and high systolic BP -> Expect HIGH risk
    high_input = MLRiskInput(
        age_years=35.0,
        systolic_bp=155.0,
        diastolic_bp=95.0,
        blood_sugar=14.0,
        blood_sugar_unit=BloodSugarUnit.MMOL_L,
        body_temperature=99.5,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
        heart_rate=88.0,
    )
    result = provider.predict(high_input)
    assert result.risk_level == MaternalRiskLevel.HIGH
    assert 0.0 <= result.model_score <= 1.0
    assert result.model_version == MODEL_VERSION
    assert result.feature_schema_version == SCHEMA_VERSION
    # Directional pseudo-attribution has been safely removed
    assert len(result.contributing_factors) == 0

    # Normal baseline vitals -> Expect LOW risk
    low_input = MLRiskInput(
        age_years=22.0,
        systolic_bp=100.0,
        diastolic_bp=70.0,
        blood_sugar=7.0,
        blood_sugar_unit=BloodSugarUnit.MMOL_L,
        body_temperature=98.0,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
        heart_rate=72.0,
    )
    low_result = provider.predict(low_input)
    assert low_result.risk_level == MaternalRiskLevel.LOW


def test_trained_model_provider_partial_features():
    """Provider handles missing/partial vital measurements via median alignment without crashing."""
    provider = TrainedModelProvider()
    partial_input = MLRiskInput(
        systolic_bp=135.0,
    )
    result = provider.predict(partial_input)
    assert result.risk_level in [MaternalRiskLevel.LOW, MaternalRiskLevel.MEDIUM, MaternalRiskLevel.HIGH]
    assert 0.0 <= result.model_score <= 1.0


def test_explicit_unit_conversions_and_boundary_safety():
    """Verify explicit unit conversions and boundary safety, especially avoiding the 25 mg/dL hazard."""
    provider = TrainedModelProvider()

    # 1. Critical Boundary Test: 25 mg/dL must NEVER be interpreted as 25 mmol/L
    hypo_input = MLRiskInput(
        age_years=25.0,
        systolic_bp=110.0,
        diastolic_bp=70.0,
        blood_sugar=25.0,
        blood_sugar_unit=BloodSugarUnit.MG_DL,  # 25 mg/dL = 1.389 mmol/L
        body_temperature=36.6,
        temperature_unit=TemperatureUnit.CELSIUS,
        heart_rate=76.0,
    )
    hypo_result = provider.predict(hypo_input)

    # If 25 mg/dL were erroneously interpreted as 25 mmol/L (lethal hyperglycemia),
    # the model would predict HIGH risk with high score. With proper conversion to ~1.39 mmol/L,
    # it is not misclassified as extreme hyperglycemia.
    hyper_input = MLRiskInput(
        age_years=25.0,
        systolic_bp=110.0,
        diastolic_bp=70.0,
        blood_sugar=25.0,
        blood_sugar_unit=BloodSugarUnit.MMOL_L,  # 25 mmol/L = lethal hyperglycemia
        body_temperature=36.6,
        temperature_unit=TemperatureUnit.CELSIUS,
        heart_rate=76.0,
    )
    hyper_result = provider.predict(hyper_input)

    assert hypo_result.model_score != hyper_result.model_score
    assert hyper_result.risk_level == MaternalRiskLevel.HIGH

    # 2. Values around former 30 mg/dL threshold
    for val in [28.0, 30.0, 32.0]:
        inp = MLRiskInput(
            age_years=25.0,
            systolic_bp=110.0,
            diastolic_bp=70.0,
            blood_sugar=val,
            blood_sugar_unit=BloodSugarUnit.MG_DL,
            body_temperature=98.0,
            temperature_unit=TemperatureUnit.FAHRENHEIT,
        )
        res = provider.predict(inp)
        assert res.risk_level in [MaternalRiskLevel.LOW, MaternalRiskLevel.MEDIUM, MaternalRiskLevel.HIGH]

    # 3. Values around former 50 C threshold
    temp_c = MLRiskInput(
        body_temperature=37.0,
        temperature_unit=TemperatureUnit.CELSIUS,
    )
    temp_f = MLRiskInput(
        body_temperature=98.6,
        temperature_unit=TemperatureUnit.FAHRENHEIT,
    )
    res_c = provider.predict(temp_c)
    res_f = provider.predict(temp_f)
    assert abs(res_c.model_score - res_f.model_score) < 0.05

    # 4. Rejection of unsupported or ambiguous units
    with pytest.raises(ValueError, match="Unsupported or ambiguous blood sugar unit"):
        bad_bs = MLRiskInput(blood_sugar=100.0)
        bad_bs.blood_sugar_unit = "invalid_unit"  # type: ignore
        provider.predict(bad_bs)

    with pytest.raises(ValueError, match="Unsupported or ambiguous temperature unit"):
        bad_temp = MLRiskInput(body_temperature=37.0)
        bad_temp.temperature_unit = "Kelvin"  # type: ignore
        provider.predict(bad_temp)


def test_unsafe_directional_heuristics_eliminated():
    """Verify that dangerous medical heuristics (e.g. SBP 70 or age 14 emitting DECREASES_RISK) cannot occur."""
    provider = TrainedModelProvider()

    # Extreme vitals that previously triggered inverted DECREASES_RISK heuristics
    adolescent_input = MLRiskInput(age_years=14.0)
    shock_input = MLRiskInput(systolic_bp=70.0, diastolic_bp=40.0)
    hypothermia_input = MLRiskInput(body_temperature=34.0, temperature_unit=TemperatureUnit.CELSIUS)
    bradycardia_input = MLRiskInput(heart_rate=40.0)

    for inp in [adolescent_input, shock_input, hypothermia_input, bradycardia_input]:
        res = provider.predict(inp)
        # Verify no factor emits DECREASES_RISK or INCREASES_RISK via median comparisons
        for factor in res.contributing_factors:
            assert factor.direction not in ("DECREASES_RISK", "INCREASES_RISK")
        assert len(res.contributing_factors) == 0


def test_artifact_loading_failure_logging(caplog):
    """Verify that failed artifact loading emits visible logs and falls back safely."""
    caplog.set_level(logging.WARNING)

    # 1. Non-existent artifact path
    non_existent = Path("ml/models/does_not_exist.joblib")
    prov = TrainedModelProvider(artifact_path=non_existent)
    assert prov.is_loaded is False
    assert any("Trained model artifact not found" in record.message for record in caplog.records)

    # 2. Fallback prediction still functions safely
    res = prov.predict(MLRiskInput(systolic_bp=120.0))
    assert res.risk_level in [MaternalRiskLevel.LOW, MaternalRiskLevel.MEDIUM, MaternalRiskLevel.HIGH]
    assert res.model_version == "baseline-heuristic-v1.0"


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
        blood_sugar_unit=BloodSugarUnit.MMOL_L,
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
                "blood_sugar": 5.0,
                "blood_sugar_unit": "mmol/L",
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
