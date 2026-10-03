"""Prediction and clinical decision orchestration service."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from backend.app.auth.dependencies import verify_patient_access
from backend.app.db.repositories import get_repository
from backend.app.ml.service import get_ml_service
from backend.app.safety.decision import get_decision_engine
from backend.app.safety.evaluator import get_safety_engine
from backend.app.schemas.alert import AlertResponse, AlertSeverity, AlertStatus
from backend.app.schemas.auth import AuthUser
from backend.app.schemas.ml import MLRiskInput
from backend.app.schemas.mother import MaternalRiskLevel
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse


class PredictionService:
    """Service orchestrating maternal risk screening, safety evaluation, and decision resolution."""

    def __init__(self):
        self.repo = get_repository()
        self.safety = get_safety_engine()
        self.ml = get_ml_service()
        self.decision = get_decision_engine()

    def evaluate_risk(
        self,
        payload: PredictionRequest,
        current_user: AuthUser,
    ) -> PredictionResponse:
        """Execute risk screening pipeline enforcing safety precedence."""
        mother_id = current_user.id
        verify_patient_access(current_user, target_mother_id=mother_id)

        # 1. Resolve feature inputs
        features = payload.features
        if not features and payload.health_record_id:
            record = self.repo.get_health_record(payload.health_record_id)
            if record:
                features = MLRiskInput(
                    pregnancy_week=record.pregnancy_week,
                    systolic_bp=record.systolic_bp,
                    diastolic_bp=record.diastolic_bp,
                    blood_sugar=record.blood_sugar,
                    hemoglobin=record.hemoglobin,
                    weight_kg=record.weight_kg,
                    body_temperature=record.body_temperature,
                    heart_rate=record.heart_rate,
                )
        if not features:
            features = MLRiskInput()

        # 2. Step 1: Deterministic Safety Evaluation (Priority 1)
        vitals_dict = features.model_dump(exclude_unset=True)
        safety_result = self.safety.evaluate(vitals=vitals_dict)

        # 3. Step 2: ML Risk Model Inference (Priority 2)
        ml_result = self.ml.predict(features)

        # 4. Step 3: Decision Engine Synthesis (Resolves safety precedence over ML)
        decision_result = self.decision.resolve(safety_result, ml_result)

        now = datetime.now(timezone.utc)
        pred_id = uuid4()

        # 5. Persist prediction output
        prediction = PredictionResponse(
            id=pred_id,
            mother_id=mother_id,
            health_record_id=payload.health_record_id,
            risk_level=decision_result.final_risk_level,
            model_score=decision_result.model_score,
            model_version=decision_result.model_version,
            feature_schema_version=decision_result.feature_schema_version,
            contributing_factors=ml_result.contributing_factors,
            created_at=now,
        )
        saved_prediction = self.repo.add_prediction(prediction)

        # 6. Safety event logging & Alert workflow triggering if elevated
        safety_event_id: Optional[UUID] = None
        if safety_result.status.value != "CLEAR":
            safety_event_id = self.repo.add_safety_event(
                mother_id=mother_id,
                safety_status=safety_result.status.value,
                trigger_reason=decision_result.trigger_reason or "Safety condition detected",
                details={"prediction_id": str(pred_id)},
            )

        # Generate alert if screening risk level is HIGH
        # Note: Deterministic safety-to-alert mappings (such as EMERGENCY -> CRITICAL alert)
        # remain explicitly deferred pending approved clinical safety specification (docs/api_contracts.md Section 6.2).
        if decision_result.final_risk_level == MaternalRiskLevel.HIGH:
            alert_id = uuid4()
            assigned_ashas = self.repo.get_assigned_mother_ids(mother_id)
            # Find asha assigned to this mother
            assigned_asha_id = None
            for aid, a in self.repo.asha_profiles.items():
                if self.repo.is_assigned_asha(a["id"], mother_id):
                    assigned_asha_id = a["id"]
                    break

            alert = AlertResponse(
                id=alert_id,
                mother_id=mother_id,
                mother_name=self.repo.mother_profiles.get(mother_id, {}).get("full_name", "Patient"),
                asha_id=assigned_asha_id,
                severity=AlertSeverity.HIGH,
                status=AlertStatus.NEW,
                trigger_reason=decision_result.trigger_reason or f"Screening risk level: {decision_result.final_risk_level.value}",
                safety_event_id=safety_event_id,
                prediction_id=pred_id,
                created_at=now,
                updated_at=now,
            )
            self.repo.add_alert(alert)

        return saved_prediction


prediction_service = PredictionService()
