"""ASHA coordination, alert workflow, visit, and longitudinal timeline service."""

from datetime import datetime, timezone
import math
from typing import List, Optional
from uuid import UUID, uuid4

from backend.app.core.errors import ForbiddenError, NotFoundError
from backend.app.db.repositories import get_repository
from backend.app.schemas.alert import AlertResponse, AlertStatus, AlertStatusUpdate
from backend.app.schemas.auth import AuthUser, UserRole
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.followup import FollowUpCreate, FollowUpResponse, FollowUpStatus
from backend.app.schemas.mother import MaternalRiskLevel
from backend.app.schemas.timeline import RiskTimelinePoint, RiskTimelineResponse
from backend.app.schemas.visit import VisitCreate, VisitResponse, VisitStatus


class CoordinationService:
    """Service handling ASHA care coordination, alerts, visits, and timeline tracking."""

    def __init__(self):
        self.repo = get_repository()

    # --- Alerts ---

    def list_alerts(
        self,
        current_user: AuthUser,
        page: int = 1,
        size: int = 20,
    ) -> PaginatedResponse[AlertResponse]:
        """List alerts filtered by authenticated role and assignment boundary."""
        items, total = self.repo.list_alerts_for_user(
            user_id=current_user.id,
            role=current_user.role,
            page=page,
            size=size,
        )
        total_pages = math.ceil(total / size) if total > 0 else 1
        return PaginatedResponse[AlertResponse](
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
        )

    def update_alert_status(
        self,
        alert_id: UUID,
        payload: AlertStatusUpdate,
        current_user: AuthUser,
    ) -> AlertResponse:
        """Update workflow status of an alert (ASHA assigned or Admin)."""
        alert = self.repo.get_alert(alert_id)
        if not alert:
            raise NotFoundError(message=f"Alert with id '{alert_id}' was not found.")

        # Enforce ASHA assignment boundary
        if current_user.role == UserRole.ASHA:
            if not self.repo.is_assigned_asha(current_user.id, alert.mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to the mother associated with this alert.")

        return self.repo.update_alert(
            alert_id=alert_id,
            status=payload.status,
            notes=payload.notes,
            updated_by=current_user.id,
        )

    # --- Visits ---

    def create_visit(
        self,
        payload: VisitCreate,
        current_user: AuthUser,
    ) -> VisitResponse:
        """Schedule or record an ASHA visit (ASHA assigned or Admin)."""
        if current_user.role == UserRole.ASHA:
            if not self.repo.is_assigned_asha(current_user.id, payload.mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")

        visit_id = uuid4()
        now = datetime.now(timezone.utc)
        visit = VisitResponse(
            id=visit_id,
            mother_id=payload.mother_id,
            asha_id=current_user.id,
            alert_id=payload.alert_id,
            visit_date=payload.visit_date,
            status=VisitStatus.SCHEDULED,
            notes=payload.notes,
            findings=payload.findings,
            created_at=now,
        )
        return self.repo.add_visit(visit)

    # --- Follow-ups ---

    def create_followup(
        self,
        payload: FollowUpCreate,
        current_user: AuthUser,
    ) -> FollowUpResponse:
        """Schedule an ASHA follow-up task (ASHA assigned or Admin)."""
        if current_user.role == UserRole.ASHA:
            if not self.repo.is_assigned_asha(current_user.id, payload.mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")

        followup_id = uuid4()
        now = datetime.now(timezone.utc)
        followup = FollowUpResponse(
            id=followup_id,
            mother_id=payload.mother_id,
            asha_id=current_user.id,
            alert_id=payload.alert_id,
            visit_id=payload.visit_id,
            due_date=payload.due_date,
            status=FollowUpStatus.PENDING,
            notes=payload.notes,
            created_at=now,
        )
        return self.repo.add_followup(followup)

    # --- Risk Timeline ---

    def get_risk_timeline(
        self,
        mother_id: UUID,
        current_user: AuthUser,
    ) -> RiskTimelineResponse:
        """Retrieve longitudinal risk timeline enforcing strict access boundaries."""
        # Enforce authorization
        if current_user.role == UserRole.MOTHER:
            if current_user.id != mother_id:
                raise ForbiddenError(message="Mothers are forbidden from accessing another patient's risk timeline.")
        elif current_user.role == UserRole.ASHA:
            if not self.repo.is_assigned_asha(current_user.id, mother_id):
                raise ForbiddenError(message="ASHA worker is not assigned to this mother.")
        elif current_user.role != UserRole.ADMIN:
            raise ForbiddenError(message="Access denied.")

        # Build chronological timeline from predictions and records
        predictions = self.repo.list_predictions(mother_id)
        records = self.repo.list_health_records(mother_id)

        assessments: List[RiskTimelinePoint] = []
        for p in predictions:
            # Look up corresponding health record if available
            rec = self.repo.get_health_record(p.health_record_id) if p.health_record_id else None
            assessments.append(RiskTimelinePoint(
                timestamp=p.created_at,
                risk_level=p.risk_level,
                assessment_type="PREDICTION",
                trigger_reason=f"Model: {p.model_version}",
                systolic_bp=rec.systolic_bp if rec else None,
                diastolic_bp=rec.diastolic_bp if rec else None,
                hemoglobin=rec.hemoglobin if rec else None,
                blood_sugar=rec.blood_sugar if rec else None,
            ))

        # Add health records not associated with predictions as baseline assessments
        pred_rec_ids = {p.health_record_id for p in predictions if p.health_record_id}
        for r in records:
            if r.id not in pred_rec_ids:
                assessments.append(RiskTimelinePoint(
                    timestamp=r.recorded_at,
                    risk_level=MaternalRiskLevel.LOW,
                    assessment_type="HEALTH_RECORD",
                    trigger_reason="Vitals recorded",
                    systolic_bp=r.systolic_bp,
                    diastolic_bp=r.diastolic_bp,
                    hemoglobin=r.hemoglobin,
                    blood_sugar=r.blood_sugar,
                ))

        # Sort chronological descending
        assessments.sort(key=lambda x: x.timestamp, reverse=True)

        current_risk: Optional[MaternalRiskLevel] = None
        if assessments:
            current_risk = assessments[0].risk_level
        elif mother_id in self.repo.mother_profiles:
            current_risk = self.repo.mother_profiles[mother_id].get("last_risk_level")

        return RiskTimelineResponse(
            mother_id=mother_id,
            current_risk_level=current_risk or MaternalRiskLevel.LOW,
            assessments=assessments,
        )


coordination_service = CoordinationService()
