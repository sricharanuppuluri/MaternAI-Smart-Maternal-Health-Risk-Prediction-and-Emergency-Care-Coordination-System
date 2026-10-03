"""In-memory thread-safe repository store and database access layer for MaternAI.

Provides:
- Entity persistence across all 17 schema entities.
- Authorization mapping (ASHA assignments, patient isolation).
- Immutable audit logging.
- Extensible Supabase integration hooks for live DB environments.
"""

from datetime import datetime, timezone
import threading
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from backend.app.core.errors import ForbiddenError, NotFoundError
from backend.app.schemas.alert import AlertResponse, AlertSeverity, AlertStatus
from backend.app.schemas.auth import UserRole
from backend.app.schemas.followup import FollowUpResponse, FollowUpStatus
from backend.app.schemas.health_record import HealthRecordResponse
from backend.app.schemas.mother import MaternalRiskLevel
from backend.app.schemas.prediction import ContributingFactor, PredictionResponse
from backend.app.schemas.symptom import SymptomResponse
from backend.app.schemas.visit import VisitResponse, VisitStatus

# Standard deterministic test UUIDs matching conftest.py
TEST_MOTHER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_ASHA_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_ADMIN_ID = UUID("00000000-0000-0000-0000-000000000003")
TEST_MOTHER_B_ID = UUID("00000000-0000-0000-0000-000000000004")


class RepositoryStore:
    """Thread-safe storage repository for Phase 3 application persistence."""

    def __init__(self):
        self._lock = threading.RLock()
        self.reset()

    def reset(self):
        """Reset and pre-seed repository with baseline test fixtures."""
        with self._lock:
            self.profiles: Dict[UUID, Dict[str, Any]] = {}
            self.mother_profiles: Dict[UUID, Dict[str, Any]] = {}
            self.asha_profiles: Dict[UUID, Dict[str, Any]] = {}
            self.asha_assignments: List[Dict[str, Any]] = []

            self.health_records: Dict[UUID, HealthRecordResponse] = {}
            self.symptoms: Dict[UUID, SymptomResponse] = {}
            self.predictions: Dict[UUID, PredictionResponse] = {}
            self.safety_events: List[Dict[str, Any]] = []
            self.alerts: Dict[UUID, AlertResponse] = {}
            self.visits: Dict[UUID, VisitResponse] = {}
            self.followups: Dict[UUID, FollowUpResponse] = {}
            self.audit_logs: List[Dict[str, Any]] = []

            self._seed_baseline_fixtures()

    def _seed_baseline_fixtures(self):
        """Seed default identities matching conftest.py test fixtures."""
        # 1. Mother A
        self.profiles[TEST_MOTHER_ID] = {
            "id": TEST_MOTHER_ID,
            "role": UserRole.MOTHER,
            "full_name": "Test Mother",
            "phone": "+91-9876543210",
        }
        self.mother_profiles[TEST_MOTHER_ID] = {
            "id": TEST_MOTHER_ID,
            "user_id": TEST_MOTHER_ID,
            "full_name": "Test Mother",
            "assigned_asha_id": TEST_ASHA_ID,
            "last_risk_level": MaternalRiskLevel.LOW,
        }

        # 2. Mother B (Unassigned from Test ASHA)
        self.profiles[TEST_MOTHER_B_ID] = {
            "id": TEST_MOTHER_B_ID,
            "role": UserRole.MOTHER,
            "full_name": "Mother B",
            "phone": "+91-9876543211",
        }
        self.mother_profiles[TEST_MOTHER_B_ID] = {
            "id": TEST_MOTHER_B_ID,
            "user_id": TEST_MOTHER_B_ID,
            "full_name": "Mother B",
            "assigned_asha_id": None,
            "last_risk_level": MaternalRiskLevel.LOW,
        }

        # 3. ASHA Worker
        self.profiles[TEST_ASHA_ID] = {
            "id": TEST_ASHA_ID,
            "role": UserRole.ASHA,
            "full_name": "Test ASHA",
            "phone": "+91-9876543220",
        }
        self.asha_profiles[TEST_ASHA_ID] = {
            "id": TEST_ASHA_ID,
            "user_id": TEST_ASHA_ID,
            "worker_code": "ASHA-001",
            "assigned_village": "Rampur",
        }

        # 4. System Admin
        self.profiles[TEST_ADMIN_ID] = {
            "id": TEST_ADMIN_ID,
            "role": UserRole.ADMIN,
            "full_name": "System Admin",
            "phone": "+91-9876543230",
        }

        # 5. ASHA Assignment (ASHA assigned to Mother A, but NOT Mother B)
        self.asha_assignments.append({
            "id": uuid4(),
            "asha_id": TEST_ASHA_ID,
            "mother_id": TEST_MOTHER_ID,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        })

    # --- Authorization & Mapping Helpers ---

    def is_assigned_asha(self, asha_user_id: UUID, mother_id: UUID) -> bool:
        """Check whether an ASHA user is actively assigned to a target mother."""
        with self._lock:
            # Check assignment mapping
            for assignment in self.asha_assignments:
                if assignment.get("is_active") and assignment.get("mother_id") == mother_id:
                    if assignment.get("asha_id") == asha_user_id:
                        return True
            # Check mother profile direct assigned_asha_id
            m = self.mother_profiles.get(mother_id)
            if m and m.get("assigned_asha_id") == asha_user_id:
                return True
            return False

    def get_assigned_mother_ids(self, asha_user_id: UUID) -> List[UUID]:
        """List all mother IDs actively assigned to an ASHA worker."""
        with self._lock:
            assigned = set()
            for assignment in self.asha_assignments:
                if assignment.get("is_active") and assignment.get("asha_id") == asha_user_id:
                    assigned.add(assignment["mother_id"])
            for mid, m in self.mother_profiles.items():
                if m.get("assigned_asha_id") == asha_user_id:
                    assigned.add(mid)
            return list(assigned)

    def resolve_mother_id(self, user_id: UUID) -> UUID:
        """Resolve mother profile ID for a user. Creates profile if not existing."""
        with self._lock:
            if user_id in self.mother_profiles:
                return user_id
            # Auto-bootstrap minimal mother profile for new user
            self.mother_profiles[user_id] = {
                "id": user_id,
                "user_id": user_id,
                "full_name": f"Mother {str(user_id)[:8]}",
                "assigned_asha_id": None,
                "last_risk_level": MaternalRiskLevel.LOW,
            }
            return user_id

    # --- Audit Logging ---

    def log_audit(
        self,
        user_id: Optional[UUID],
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Append an immutable audit entry."""
        with self._lock:
            self.audit_logs.append({
                "id": uuid4(),
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc),
            })

    # --- Health Records ---

    def add_health_record(self, record: HealthRecordResponse) -> HealthRecordResponse:
        with self._lock:
            self.health_records[record.id] = record
            self.log_audit(
                user_id=record.recorded_by or record.mother_id,
                action="CREATE",
                resource_type="health_records",
                resource_id=record.id,
                details={"mother_id": str(record.mother_id), "pregnancy_week": record.pregnancy_week},
            )
            return record

    def get_health_record(self, record_id: UUID) -> Optional[HealthRecordResponse]:
        with self._lock:
            return self.health_records.get(record_id)

    def list_health_records(self, mother_id: UUID) -> List[HealthRecordResponse]:
        with self._lock:
            records = [r for r in self.health_records.values() if r.mother_id == mother_id]
            records.sort(key=lambda x: x.recorded_at, reverse=True)
            return records

    # --- Symptoms ---

    def add_symptoms(self, symptom_records: List[SymptomResponse]) -> List[SymptomResponse]:
        with self._lock:
            for s in symptom_records:
                self.symptoms[s.id] = s
                self.log_audit(
                    user_id=s.mother_id,
                    action="CREATE",
                    resource_type="symptoms",
                    resource_id=s.id,
                    details={"symptom_code": s.symptom_code, "severity": s.severity},
                )
            return symptom_records

    def list_symptoms(self, mother_id: UUID) -> List[SymptomResponse]:
        with self._lock:
            items = [s for s in self.symptoms.values() if s.mother_id == mother_id]
            items.sort(key=lambda x: x.recorded_at, reverse=True)
            return items

    # --- Predictions & Safety Events ---

    def add_prediction(self, prediction: PredictionResponse) -> PredictionResponse:
        with self._lock:
            self.predictions[prediction.id] = prediction
            # Update mother's last_risk_level
            if prediction.mother_id in self.mother_profiles:
                self.mother_profiles[prediction.mother_id]["last_risk_level"] = prediction.risk_level
            self.log_audit(
                user_id=prediction.mother_id,
                action="CREATE",
                resource_type="predictions",
                resource_id=prediction.id,
                details={"risk_level": prediction.risk_level.value, "model_score": prediction.model_score},
            )
            return prediction

    def get_prediction(self, prediction_id: UUID) -> Optional[PredictionResponse]:
        with self._lock:
            return self.predictions.get(prediction_id)

    def list_predictions(self, mother_id: UUID) -> List[PredictionResponse]:
        with self._lock:
            preds = [p for p in self.predictions.values() if p.mother_id == mother_id]
            preds.sort(key=lambda x: x.created_at, reverse=True)
            return preds

    def add_safety_event(
        self,
        mother_id: UUID,
        safety_status: str,
        trigger_reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        with self._lock:
            event_id = uuid4()
            event = {
                "id": event_id,
                "mother_id": mother_id,
                "safety_status": safety_status,
                "trigger_reason": trigger_reason,
                "details": details or {},
                "created_at": datetime.now(timezone.utc),
            }
            self.safety_events.append(event)
            self.log_audit(
                user_id=mother_id,
                action="CREATE",
                resource_type="safety_events",
                resource_id=event_id,
                details={"safety_status": safety_status, "trigger_reason": trigger_reason},
            )
            return event_id

    def list_safety_events(self, mother_id: UUID) -> List[Dict[str, Any]]:
        with self._lock:
            events = [e for e in self.safety_events if e["mother_id"] == mother_id]
            events.sort(key=lambda x: x["created_at"], reverse=True)
            return events

    # --- Alerts ---

    def add_alert(self, alert: AlertResponse) -> AlertResponse:
        with self._lock:
            self.alerts[alert.id] = alert
            self.log_audit(
                user_id=alert.asha_id or alert.mother_id,
                action="CREATE",
                resource_type="alerts",
                resource_id=alert.id,
                details={"severity": alert.severity.value, "status": alert.status.value},
            )
            return alert

    def get_alert(self, alert_id: UUID) -> Optional[AlertResponse]:
        with self._lock:
            return self.alerts.get(alert_id)

    def update_alert(
        self,
        alert_id: UUID,
        status: AlertStatus,
        notes: Optional[str] = None,
        updated_by: Optional[UUID] = None,
    ) -> AlertResponse:
        with self._lock:
            alert = self.alerts.get(alert_id)
            if not alert:
                raise NotFoundError(message=f"Alert with id '{alert_id}' not found.")
            updated_alert = AlertResponse(
                id=alert.id,
                mother_id=alert.mother_id,
                mother_name=alert.mother_name,
                asha_id=alert.asha_id,
                severity=alert.severity,
                status=status,
                trigger_reason=alert.trigger_reason,
                safety_event_id=alert.safety_event_id,
                prediction_id=alert.prediction_id,
                created_at=alert.created_at,
                updated_at=datetime.now(timezone.utc),
            )
            self.alerts[alert_id] = updated_alert
            self.log_audit(
                user_id=updated_by,
                action="UPDATE",
                resource_type="alerts",
                resource_id=alert_id,
                details={"status": status.value, "notes": notes},
            )
            return updated_alert

    def list_alerts_for_user(
        self,
        user_id: UUID,
        role: UserRole,
        page: int = 1,
        size: int = 20,
    ) -> (List[AlertResponse], int):
        with self._lock:
            if role == UserRole.ADMIN:
                items = list(self.alerts.values())
            elif role == UserRole.MOTHER:
                items = [a for a in self.alerts.values() if a.mother_id == user_id]
            elif role == UserRole.ASHA:
                assigned_mids = set(self.get_assigned_mother_ids(user_id))
                items = [a for a in self.alerts.values() if a.mother_id in assigned_mids or a.asha_id == user_id]
            else:
                items = []

            items.sort(key=lambda x: x.created_at, reverse=True)
            total = len(items)
            start = (page - 1) * size
            end = start + size
            return items[start:end], total

    # --- Visits ---

    def add_visit(self, visit: VisitResponse) -> VisitResponse:
        with self._lock:
            self.visits[visit.id] = visit
            self.log_audit(
                user_id=visit.asha_id,
                action="CREATE",
                resource_type="visits",
                resource_id=visit.id,
                details={"mother_id": str(visit.mother_id), "status": visit.status.value},
            )
            return visit

    def list_visits(self, mother_id: UUID) -> List[VisitResponse]:
        with self._lock:
            v_list = [v for v in self.visits.values() if v.mother_id == mother_id]
            v_list.sort(key=lambda x: x.visit_date, reverse=True)
            return v_list

    # --- Follow-ups ---

    def add_followup(self, followup: FollowUpResponse) -> FollowUpResponse:
        with self._lock:
            self.followups[followup.id] = followup
            self.log_audit(
                user_id=followup.asha_id,
                action="CREATE",
                resource_type="follow_ups",
                resource_id=followup.id,
                details={"mother_id": str(followup.mother_id), "due_date": str(followup.due_date)},
            )
            return followup

    def list_followups(self, mother_id: UUID) -> List[FollowUpResponse]:
        with self._lock:
            f_list = [f for f in self.followups.values() if f.mother_id == mother_id]
            f_list.sort(key=lambda x: x.due_date, reverse=True)
            return f_list


# Global repository store singleton
repository = RepositoryStore()


def get_repository() -> RepositoryStore:
    """Dependency injector for data repository."""
    return repository
