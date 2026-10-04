"""Trained machine learning model provider for MaternAI Phase 5.

Loads the versioned scikit-learn model artifact trained on the official UCI Maternal Health Risk dataset.
Provides:
- Schema validation against supported vital measurements.
- Explicit canonical-unit conversion (mg/dL -> mmol/L, °C -> °F) without magic numeric thresholds.
- Preprocessing and feature alignment (Age, SystolicBP, DiastolicBP, BS, BodyTemp, HeartRate).
- Prediction output strictly matching MLPredictionResult and MaternalRiskLevel (LOW, MEDIUM, HIGH).
- Removal of unsafe hardcoded directional pseudo-attribution.
- Observable operational logging on artifact loading failures.
- Fallback/missing artifact resilience for local test isolation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
import joblib
import numpy as np
import pandas as pd

from backend.app.ml.preprocessor import FEATURE_COLS, FeatureImputerAndAligner
from backend.app.ml.service import BaselineScreeningModel, MLPredictionResult, ModelProvider
from backend.app.schemas.ml import BloodSugarUnit, MLRiskInput, TemperatureUnit
from backend.app.schemas.mother import MaternalRiskLevel
from backend.app.schemas.prediction import ContributingFactor

logger = logging.getLogger(__name__)

# Default path to serialized model artifact
DEFAULT_ARTIFACT_PATH = Path("ml/models/maternal_risk_model_v1.joblib")


class TrainedModelProvider(ModelProvider):
    """Production trained model provider loading serialized Gradient Boosting pipeline artifact."""

    def __init__(self, artifact_path: Optional[Path] = None):
        self.artifact_path = artifact_path or DEFAULT_ARTIFACT_PATH
        self._artifact = None
        self._fallback = BaselineScreeningModel()
        self._load_artifact()

    def _load_artifact(self):
        """Loads serialized model pipeline and metadata with observable logging."""
        if self.artifact_path.exists():
            try:
                self._artifact = joblib.load(self.artifact_path)
                logger.info("Successfully loaded trained maternal risk model artifact from %s", self.artifact_path)
            except Exception as exc:
                logger.error(
                    "Failed to load trained model artifact from %s: %s. Operating in baseline fallback mode.",
                    self.artifact_path,
                    exc,
                )
                self._artifact = None
        else:
            logger.warning(
                "Trained model artifact not found at %s. Operating in baseline fallback mode.",
                self.artifact_path,
            )
            self._artifact = None

    @property
    def is_loaded(self) -> bool:
        """Indicates if the trained model artifact is active."""
        return self._artifact is not None

    def predict(self, features: MLRiskInput) -> MLPredictionResult:
        """Executes inference using the trained gradient boosting model or fallback if unconfigured."""
        if not self.is_loaded:
            return self._fallback.predict(features)

        pipeline = self._artifact["pipeline"]
        feature_cols = self._artifact["feature_cols"]
        model_version = self._artifact.get("model_version", "gradient-boosting-v1.0")
        feature_schema_version = self._artifact.get("feature_schema_version", "schema-v1")

        # 1. Resolve explicit body temperature unit
        # Model canonical unit: Fahrenheit (°F)
        temp_val = features.body_temperature
        if temp_val is not None:
            unit_temp = features.temperature_unit
            if unit_temp == TemperatureUnit.CELSIUS or str(unit_temp).upper() in ("C", "CELSIUS"):
                temp_val = (temp_val * 9.0 / 5.0) + 32.0
            elif unit_temp == TemperatureUnit.FAHRENHEIT or str(unit_temp).upper() in ("F", "FAHRENHEIT"):
                temp_val = float(temp_val)
            else:
                raise ValueError(
                    f"Unsupported or ambiguous temperature unit: '{unit_temp}'. Must be 'C' or 'F'."
                )

        # 2. Resolve explicit blood glucose unit
        # Model canonical unit: mmol/L (standard for UCI Maternal Health Risk dataset)
        bs_val = features.blood_sugar
        if bs_val is not None:
            unit_bs = features.blood_sugar_unit
            if unit_bs == BloodSugarUnit.MG_DL or str(unit_bs) in ("mg/dL", "mg/dl"):
                bs_val = float(bs_val) / 18.0
            elif unit_bs == BloodSugarUnit.MMOL_L or str(unit_bs) in ("mmol/L", "mmol/l"):
                bs_val = float(bs_val)
            else:
                raise ValueError(
                    f"Unsupported or ambiguous blood sugar unit: '{unit_bs}'. Must be 'mg/dL' or 'mmol/L'."
                )

        feature_dict = {
            "Age": features.age_years,
            "SystolicBP": features.systolic_bp,
            "DiastolicBP": features.diastolic_bp,
            "BS": bs_val,
            "BodyTemp": temp_val,
            "HeartRate": features.heart_rate,
        }

        input_df = pd.DataFrame([feature_dict])[feature_cols]

        # Predict risk class
        preds = pipeline.predict(input_df)
        predicted_label = preds[0]  # "LOW", "MEDIUM", or "HIGH"

        # Predict class probabilities
        probs = pipeline.predict_proba(input_df)[0]
        classes = list(pipeline.classes_)

        # Internal model score: probability assigned to HIGH risk, or top predicted class probability
        high_idx = classes.index("HIGH") if "HIGH" in classes else None
        pred_idx = classes.index(predicted_label)

        # Internal screening metric (0.0 to 1.0)
        # Note: Strictly internal model metric; not a clinical probability
        model_score = round(float(probs[high_idx] if high_idx is not None else probs[pred_idx]), 4)

        # Map to canonical MaternalRiskLevel
        risk_level = MaternalRiskLevel(predicted_label)

        # Per architectural requirement: Unsafe hardcoded directional clinical heuristics
        # (e.g. comparing vitals to population medians and labeling INCREASES_RISK / DECREASES_RISK)
        # are removed. No unsupported directional claims are produced.
        contributing_factors: List[ContributingFactor] = []

        return MLPredictionResult(
            risk_level=risk_level,
            model_score=model_score,
            model_version=model_version,
            feature_schema_version=feature_schema_version,
            contributing_factors=contributing_factors,
        )
