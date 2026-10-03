"""Health record and symptom management service layer."""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from backend.app.auth.dependencies import verify_patient_access
from backend.app.db.repositories import get_repository
from backend.app.safety.evaluator import get_safety_engine
from backend.app.schemas.auth import AuthUser, UserRole
from backend.app.schemas.health_record import HealthRecordCreate, HealthRecordResponse
from backend.app.schemas.symptom import SymptomResponse, SymptomSubmission


class HealthRecordService:
    """Service handling maternal health measurements and vital sign logging."""

    def __init__(self):
        self.repo = get_repository()
        self.safety = get_safety_engine()

    def create_health_record(
        self,
        payload: HealthRecordCreate,
        current_user: AuthUser,
    ) -> HealthRecordResponse:
        """Create and persist a new health record."""
        # Resolve target mother
        mother_id = current_user.id

        # Verify access authorization
        verify_patient_access(current_user, target_mother_id=mother_id)

        # Build domain response object
        record_id = uuid4()
        now = datetime.now(timezone.utc)
        record = HealthRecordResponse(
            id=record_id,
            mother_id=mother_id,
            pregnancy_week=payload.pregnancy_week,
            systolic_bp=payload.systolic_bp,
            diastolic_bp=payload.diastolic_bp,
            blood_sugar=payload.blood_sugar,
            hemoglobin=payload.hemoglobin,
            weight_kg=payload.weight_kg,
            body_temperature=payload.body_temperature,
            heart_rate=payload.heart_rate,
            recorded_by=current_user.id,
            recorded_at=payload.recorded_at or now,
            created_at=now,
        )

        # Deterministic safety evaluation boundary
        vitals_dict = payload.model_dump(exclude_unset=True)
        safety_result = self.safety.evaluate(vitals=vitals_dict)
        if safety_result.is_emergency or safety_result.status.value != "CLEAR":
            self.repo.add_safety_event(
                mother_id=mother_id,
                safety_status=safety_result.status.value,
                trigger_reason=", ".join(safety_result.triggered_rules) or "Vital signs safety event",
                details={"health_record_id": str(record_id)},
            )

        # Persist record
        return self.repo.add_health_record(record)


class SymptomService:
    """Service handling maternal symptom logging."""

    def __init__(self):
        self.repo = get_repository()
        self.safety = get_safety_engine()

    def record_symptoms(
        self,
        payload: SymptomSubmission,
        current_user: AuthUser,
    ) -> List[SymptomResponse]:
        """Record and persist maternal symptoms."""
        mother_id = current_user.id
        verify_patient_access(current_user, target_mother_id=mother_id)

        now = datetime.now(timezone.utc)
        results: List[SymptomResponse] = []

        symptoms_eval = []
        for item in payload.symptoms:
            s_id = uuid4()
            s_record = SymptomResponse(
                id=s_id,
                mother_id=mother_id,
                health_record_id=payload.health_record_id,
                symptom_code=item.symptom_code,
                severity=item.severity,
                notes=item.notes,
                recorded_at=now,
                created_at=now,
            )
            results.append(s_record)
            symptoms_eval.append({"symptom_code": item.symptom_code, "severity": item.severity})

        # Deterministic safety evaluation boundary on symptoms
        safety_result = self.safety.evaluate(symptoms=symptoms_eval)
        if safety_result.is_emergency or safety_result.status.value != "CLEAR":
            self.repo.add_safety_event(
                mother_id=mother_id,
                safety_status=safety_result.status.value,
                trigger_reason=", ".join(safety_result.triggered_rules) or "Symptom safety event",
                details={"health_record_id": str(payload.health_record_id) if payload.health_record_id else None},
            )

        # Persist symptoms
        return self.repo.add_symptoms(results)


health_record_service = HealthRecordService()
symptom_service = SymptomService()
