"""Trained machine learning model provider for MaternAI Phase 5.

Loads the versioned scikit-learn model artifact trained on the official UCI Maternal Health Risk dataset.
Provides:
- Schema validation against supported vital measurements.
- Preprocessing and feature alignment (Age, SystolicBP, DiastolicBP, BS, BodyTemp, HeartRate).
- Prediction output strictly matching MLPredictionResult and MaternalRiskLevel (LOW, MEDIUM, HIGH).
- Feature influence / contributing factors based on feature importance and patient directional deviation.
- Fallback/missing artifact resilience for local test isolation.
"""

from pathlib import Path
from typing import Dict, List, Optional
import joblib
import numpy as np
import pandas as pd

from backend.app.ml.preprocessor import FEATURE_COLS, FeatureImputerAndAligner
from backend.app.ml.service import BaselineScreeningModel, MLPredictionResult, ModelProvider
from backend.app.schemas.ml import MLRiskInput
from backend.app.schemas.mother import MaternalRiskLevel
from backend.app.schemas.prediction import ContributingFactor

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
        """Loads serialized model pipeline and metadata."""
        if self.artifact_path.exists():
            try:
                self._artifact = joblib.load(self.artifact_path)
            except Exception:
                self._artifact = None
        else:
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
        feature_importances: Dict[str, float] = self._artifact.get("feature_importances", {})

        # Extract features from MLRiskInput
        # Note: If body_temperature is provided in Celsius (< 50), convert to Fahrenheit (°F) for model alignment
        temp_val = features.body_temperature
        if temp_val is not None and temp_val < 50.0:
            temp_val = (temp_val * 9.0 / 5.0) + 32.0

        # Note: If blood_sugar is provided in mg/dL (> 30), convert to mmol/L (/ 18.0) for model alignment
        bs_val = features.blood_sugar
        if bs_val is not None and bs_val > 30.0:
            bs_val = bs_val / 18.0

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

        # Calculate contributing factors using feature importances and directional signs
        contributing_factors: List[ContributingFactor] = []

        # Population medians / reference baselines from training data
        ref_baselines = {
            "Age": 25.0,
            "SystolicBP": 120.0,
            "DiastolicBP": 80.0,
            "BS": 7.5,
            "BodyTemp": 98.0,
            "HeartRate": 76.0,
        }

        for feat_name in feature_cols:
            observed_val = feature_dict.get(feat_name)
            if observed_val is not None:
                ref_val = ref_baselines.get(feat_name, observed_val)
                # If feature is higher than reference for adverse vitals, it increases risk
                if observed_val > ref_val:
                    direction = "INCREASES_RISK"
                elif observed_val < ref_val:
                    direction = "DECREASES_RISK"
                else:
                    direction = "NEUTRAL"

                contributing_factors.append(
                    ContributingFactor(
                        feature=feat_name,
                        direction=direction,
                        value=round(float(observed_val), 2),
                    )
                )

        # Sort contributing factors by model feature importance
        contributing_factors.sort(
            key=lambda cf: feature_importances.get(cf.feature, 0.0),
            reverse=True,
        )

        return MLPredictionResult(
            risk_level=risk_level,
            model_score=model_score,
            model_version=model_version,
            feature_schema_version=feature_schema_version,
            contributing_factors=contributing_factors,
        )
