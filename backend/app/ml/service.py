"""Machine Learning prediction service and provider boundary.

Contract Invariants:
- Categorical risk classification: LOW, MEDIUM, HIGH.
- model_score is an internal model metric (0.0 - 1.0), NOT a calibrated medical probability.
- Real model training and artifact deployment is scheduled for Phase 5.
- ModelProvider interface ensures modular model swapping without changing API contracts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from backend.app.schemas.ml import MLRiskInput
from backend.app.schemas.mother import MaternalRiskLevel
from backend.app.schemas.prediction import ContributingFactor


@dataclass
class MLPredictionResult:
    """Internal screening prediction result from an ML model provider."""
    risk_level: MaternalRiskLevel
    model_score: float
    model_version: str
    feature_schema_version: str
    contributing_factors: List[ContributingFactor] = field(default_factory=list)


class ModelProvider(ABC):
    """Abstract interface for maternal health risk screening models."""

    @abstractmethod
    def predict(self, features: MLRiskInput) -> MLPredictionResult:
        """Execute risk screening inference on input features."""
        pass


class BaselineScreeningModel(ModelProvider):
    """Baseline rule-guided screening provider used until trained Phase 5 model artifacts are deployed.
    
    Provides deterministic baseline scoring and explainability factors.
    model_score reflects an internal screening score, NOT a medical probability.
    """

    def predict(self, features: MLRiskInput) -> MLPredictionResult:
        factors: List[ContributingFactor] = []
        score = 0.25
        risk = MaternalRiskLevel.LOW

        # Feature influence inspection (data-integrity heuristics, non-diagnostic)
        if features.systolic_bp is not None:
            if features.systolic_bp >= 140.0:
                score += 0.35
                factors.append(ContributingFactor(
                    feature="systolic_bp",
                    direction="INCREASES_RISK",
                    value=features.systolic_bp,
                ))
            elif features.systolic_bp <= 120.0:
                factors.append(ContributingFactor(
                    feature="systolic_bp",
                    direction="DECREASES_RISK",
                    value=features.systolic_bp,
                ))

        if features.blood_sugar is not None:
            if features.blood_sugar >= 140.0:
                score += 0.25
                factors.append(ContributingFactor(
                    feature="blood_sugar",
                    direction="INCREASES_RISK",
                    value=features.blood_sugar,
                ))

        if features.hemoglobin is not None:
            if features.hemoglobin < 11.0:
                score += 0.20
                factors.append(ContributingFactor(
                    feature="hemoglobin",
                    direction="INCREASES_RISK",
                    value=features.hemoglobin,
                ))

        # Clamp model score to [0.0, 1.0] internal metric range
        score = round(min(max(score, 0.0), 1.0), 4)

        if score >= 0.70:
            risk = MaternalRiskLevel.HIGH
        elif score >= 0.40:
            risk = MaternalRiskLevel.MEDIUM
        else:
            risk = MaternalRiskLevel.LOW

        return MLPredictionResult(
            risk_level=risk,
            model_score=score,
            model_version="baseline-heuristic-v1.0",
            feature_schema_version="schema-v1",
            contributing_factors=factors,
        )


class MLPredictionService:
    """Service facade coordinating model inference."""

    def __init__(self, provider: Optional[ModelProvider] = None):
        self._provider = provider or BaselineScreeningModel()

    def set_provider(self, provider: ModelProvider):
        """Allow injecting future trained ML model providers."""
        self._provider = provider

    def predict(self, features: MLRiskInput) -> MLPredictionResult:
        return self._provider.predict(features)


# Global ML prediction service instance
ml_service = MLPredictionService()


def get_ml_service() -> MLPredictionService:
    """Dependency provider for ML prediction service."""
    return ml_service
