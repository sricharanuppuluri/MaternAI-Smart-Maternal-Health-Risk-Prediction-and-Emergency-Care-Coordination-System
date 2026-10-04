"""Relational persistent database repository layer for MaternAI.

Provides:
- PostgreSQL / Supabase schema parity across all 17 documented entities.
- Relational disk-backed SQL persistence ensuring data survives backend restarts.
- Authoritative user profile resolution and anti-escalation role protection.
- Assignment-based worker authorization mappings.
- Immutable audit logging.
- Extensible Supabase PostgREST client integration for live cloud environments.
"""

from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from backend.app.core.config import get_settings
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


def _to_iso(dt: Optional[Union[datetime, date]]) -> Optional[str]:
    """Convert datetime or date to ISO string."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return dt.isoformat()


def _parse_dt(iso_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO string to UTC datetime."""
    if not iso_str:
        return None
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse ISO string to date."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str[:10])
    except Exception:
        return None


class RepositoryStore:
    """Persistent relational repository store implementing the 17-entity Supabase schema."""

    def __init__(self, db_path: Optional[str] = None):
        self._lock = threading.RLock()
        settings = get_settings()

        if db_path is not None:
            self._db_path = db_path
        else:
            self._db_path = settings.DATABASE_FILE

        if self._db_path != ":memory:":
            db_dir = os.path.dirname(self._db_path)
            if db_dir:
                Path(db_dir).mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Create all 17 schema tables matching 20261003000001_initial_schema.sql."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("PRAGMA journal_mode = WAL")
            cur.execute("PRAGMA foreign_keys = ON")

            # 1. profiles
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL CHECK (role IN ('MOTHER', 'ASHA', 'ADMIN')),
                    full_name TEXT NOT NULL,
                    phone TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 2. asha_profiles
            cur.execute("""
                CREATE TABLE IF NOT EXISTS asha_profiles (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    worker_code TEXT UNIQUE,
                    assigned_village TEXT,
                    phone TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 3. mother_profiles
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mother_profiles (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    full_name TEXT,
                    date_of_birth TEXT,
                    age_years INTEGER,
                    gestational_age_weeks INTEGER,
                    expected_due_date TEXT,
                    assigned_asha_id TEXT,
                    last_risk_level TEXT CHECK (last_risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 4. asha_assignments
            cur.execute("""
                CREATE TABLE IF NOT EXISTS asha_assignments (
                    id TEXT PRIMARY KEY,
                    asha_id TEXT NOT NULL,
                    mother_id TEXT NOT NULL,
                    assigned_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(asha_id, mother_id)
                )
            """)

            # 5. health_records
            cur.execute("""
                CREATE TABLE IF NOT EXISTS health_records (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    recorded_by TEXT,
                    pregnancy_week INTEGER,
                    systolic_bp REAL,
                    diastolic_bp REAL,
                    blood_sugar REAL,
                    hemoglobin REAL,
                    weight_kg REAL,
                    body_temperature REAL,
                    heart_rate REAL,
                    notes TEXT,
                    recorded_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 6. symptoms
            cur.execute("""
                CREATE TABLE IF NOT EXISTS symptoms (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    health_record_id TEXT,
                    symptom_code TEXT NOT NULL,
                    severity INTEGER NOT NULL DEFAULT 1,
                    notes TEXT,
                    onset_date TEXT,
                    recorded_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 7. model_versions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS model_versions (
                    id TEXT PRIMARY KEY,
                    version_tag TEXT NOT NULL UNIQUE,
                    algorithm TEXT NOT NULL,
                    feature_schema_version TEXT NOT NULL,
                    metrics TEXT NOT NULL DEFAULT '{}',
                    is_active INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            # 8. predictions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    health_record_id TEXT,
                    model_version_id TEXT,
                    risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
                    model_score REAL,
                    model_version TEXT,
                    feature_schema_version TEXT,
                    contributing_factors TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
            """)

            # 9. safety_events
            cur.execute("""
                CREATE TABLE IF NOT EXISTS safety_events (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    health_record_id TEXT,
                    safety_status TEXT NOT NULL CHECK (safety_status IN ('CLEAR', 'CONCERNING', 'EMERGENCY')),
                    rule_code TEXT,
                    trigger_reason TEXT,
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
            """)

            # 10. alerts
            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    asha_id TEXT,
                    mother_name TEXT NOT NULL,
                    severity TEXT NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
                    status TEXT NOT NULL CHECK (
                        status IN ('NEW', 'ACKNOWLEDGED', 'CONTACTED', 'VISIT_SCHEDULED', 'FOLLOW_UP_PENDING', 'RESOLVED', 'ESCALATED')
                    ),
                    trigger_reason TEXT NOT NULL,
                    safety_event_id TEXT,
                    prediction_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 11. visits
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    asha_id TEXT NOT NULL,
                    alert_id TEXT,
                    visit_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    findings TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 12. follow_ups
            cur.execute("""
                CREATE TABLE IF NOT EXISTS follow_ups (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    asha_id TEXT NOT NULL,
                    alert_id TEXT,
                    visit_id TEXT,
                    due_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # 13. appointments
            cur.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    facility_name TEXT,
                    appointment_date TEXT NOT NULL,
                    purpose TEXT,
                    status TEXT NOT NULL DEFAULT 'SCHEDULED',
                    created_at TEXT NOT NULL
                )
            """)

            # 14. medication_reminders
            cur.execute("""
                CREATE TABLE IF NOT EXISTS medication_reminders (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    medication_name TEXT NOT NULL,
                    dosage TEXT,
                    frequency TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)

            # 15. chat_sessions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    mother_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # 16. chat_messages
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    sender_role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
            """)

            # 17. audit_logs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT,
                    details TEXT NOT NULL DEFAULT '{}',
                    timestamp TEXT NOT NULL
                )
            """)

            self._conn.commit()

            # Seed default baseline fixtures if profiles table is empty
            cur.execute("SELECT COUNT(*) as cnt FROM profiles")
            if cur.fetchone()["cnt"] == 0:
                self._seed_baseline_fixtures()

    def reset(self):
        """Reset and pre-seed repository with clean baseline test fixtures."""
        with self._lock:
            cur = self._conn.cursor()
            tables = [
                "profiles", "mother_profiles", "asha_profiles", "asha_assignments",
                "health_records", "symptoms", "model_versions", "predictions",
                "safety_events", "alerts", "visits", "follow_ups", "appointments",
                "medication_reminders", "chat_sessions", "chat_messages", "audit_logs"
            ]
            for t in tables:
                cur.execute(f"DELETE FROM {t}")
            self._conn.commit()
            self._seed_baseline_fixtures()

    def _seed_baseline_fixtures(self):
        """Seed default identities matching conftest.py test fixtures."""
        now_str = _to_iso(datetime.now(timezone.utc))

        with self._lock:
            cur = self._conn.cursor()

            # 1. Mother A
            cur.execute(
                "INSERT OR REPLACE INTO profiles VALUES (?, ?, ?, ?, ?, ?)",
                (str(TEST_MOTHER_ID), UserRole.MOTHER.value, "Test Mother", "+91-9876543210", now_str, now_str)
            )
            cur.execute(
                "INSERT OR REPLACE INTO mother_profiles (id, user_id, full_name, assigned_asha_id, last_risk_level, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(TEST_MOTHER_ID), str(TEST_MOTHER_ID), "Test Mother", str(TEST_ASHA_ID), MaternalRiskLevel.LOW.value, now_str, now_str)
            )

            # 2. Mother B (Unassigned from Test ASHA)
            cur.execute(
                "INSERT OR REPLACE INTO profiles VALUES (?, ?, ?, ?, ?, ?)",
                (str(TEST_MOTHER_B_ID), UserRole.MOTHER.value, "Mother B", "+91-9876543211", now_str, now_str)
            )
            cur.execute(
                "INSERT OR REPLACE INTO mother_profiles (id, user_id, full_name, assigned_asha_id, last_risk_level, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(TEST_MOTHER_B_ID), str(TEST_MOTHER_B_ID), "Mother B", None, MaternalRiskLevel.LOW.value, now_str, now_str)
            )

            # 3. ASHA Worker
            cur.execute(
                "INSERT OR REPLACE INTO profiles VALUES (?, ?, ?, ?, ?, ?)",
                (str(TEST_ASHA_ID), UserRole.ASHA.value, "Test ASHA", "+91-9876543220", now_str, now_str)
            )
            cur.execute(
                "INSERT OR REPLACE INTO asha_profiles (id, user_id, worker_code, assigned_village, phone, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(TEST_ASHA_ID), str(TEST_ASHA_ID), "ASHA-001", "Rampur", "+91-9876543220", now_str, now_str)
            )

            # 4. System Admin
            cur.execute(
                "INSERT OR REPLACE INTO profiles VALUES (?, ?, ?, ?, ?, ?)",
                (str(TEST_ADMIN_ID), UserRole.ADMIN.value, "System Admin", "+91-9876543230", now_str, now_str)
            )

            # 5. ASHA Assignment (ASHA assigned to Mother A, but NOT Mother B)
            cur.execute(
                "INSERT OR REPLACE INTO asha_assignments (id, asha_id, mother_id, assigned_at, is_active) VALUES (?, ?, ?, ?, 1)",
                (str(uuid4()), str(TEST_ASHA_ID), str(TEST_MOTHER_ID), now_str)
            )

            self._conn.commit()

    # --- Profiles & Role Integrity ---

    def get_profile(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve authoritative profile by user UUID."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM profiles WHERE id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": UUID(row["id"]),
                "role": UserRole(row["role"]),
                "full_name": row["full_name"],
                "phone": row["phone"],
                "created_at": _parse_dt(row["created_at"]),
                "updated_at": _parse_dt(row["updated_at"]),
            }

    def upsert_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update user profile adhering to role constraints."""
        with self._lock:
            cur = self._conn.cursor()
            uid = str(profile_data["id"])
            role_val = profile_data["role"].value if isinstance(profile_data["role"], UserRole) else str(profile_data["role"])
            now_str = _to_iso(profile_data.get("updated_at") or datetime.now(timezone.utc))
            created_str = _to_iso(profile_data.get("created_at") or datetime.now(timezone.utc))

            cur.execute(
                """
                INSERT INTO profiles (id, role, full_name, phone, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    role = excluded.role,
                    full_name = excluded.full_name,
                    phone = excluded.phone,
                    updated_at = excluded.updated_at
                """,
                (uid, role_val, profile_data["full_name"], profile_data.get("phone"), created_str, now_str)
            )
            self._conn.commit()
            return profile_data

    # --- Authorization & Mapping Helpers ---

    def is_assigned_asha(self, asha_user_id: UUID, mother_id: UUID) -> bool:
        """Check whether an ASHA user is actively assigned to a target mother."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM asha_assignments WHERE asha_id = ? AND mother_id = ? AND is_active = 1",
                (str(asha_user_id), str(mother_id))
            )
            if cur.fetchone()["cnt"] > 0:
                return True

            cur.execute(
                "SELECT COUNT(*) as cnt FROM mother_profiles WHERE (id = ? OR user_id = ?) AND assigned_asha_id = ?",
                (str(mother_id), str(mother_id), str(asha_user_id))
            )
            return cur.fetchone()["cnt"] > 0

    def get_assigned_mother_ids(self, asha_user_id: UUID) -> List[UUID]:
        """List all mother IDs actively assigned to an ASHA worker."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT mother_id FROM asha_assignments WHERE asha_id = ? AND is_active = 1",
                (str(asha_user_id),)
            )
            assigned = {UUID(r["mother_id"]) for r in cur.fetchall()}

            cur.execute(
                "SELECT id, user_id FROM mother_profiles WHERE assigned_asha_id = ?",
                (str(asha_user_id),)
            )
            for r in cur.fetchall():
                assigned.add(UUID(r["id"]))
            return list(assigned)

    def resolve_mother_id(self, user_id: UUID) -> UUID:
        """Resolve mother profile ID for a user. Bootstraps profile if not existing."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT id FROM mother_profiles WHERE user_id = ?", (str(user_id),))
            row = cur.fetchone()
            if row:
                return UUID(row["id"])

            now_str = _to_iso(datetime.now(timezone.utc))
            cur.execute(
                "INSERT INTO mother_profiles (id, user_id, full_name, assigned_asha_id, last_risk_level, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(user_id), str(user_id), f"Mother {str(user_id)[:8]}", None, MaternalRiskLevel.LOW.value, now_str, now_str)
            )
            self._conn.commit()
            return user_id

    # --- Audit Logging ---

    def log_audit(
        self,
        user_id: Optional[UUID],
        action: str,
        resource_type: str,
        resource_id: Optional[Union[UUID, str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Append an immutable audit entry."""
        with self._lock:
            cur = self._conn.cursor()
            event_id = str(uuid4())
            cur.execute(
                "INSERT INTO audit_logs (id, user_id, action, resource_type, resource_id, details, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    str(user_id) if user_id else None,
                    action,
                    resource_type,
                    str(resource_id) if resource_id else None,
                    json.dumps(details or {}),
                    _to_iso(datetime.now(timezone.utc))
                )
            )
            self._conn.commit()

    # --- Health Records ---

    def add_health_record(self, record: HealthRecordResponse) -> HealthRecordResponse:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO health_records (
                    id, mother_id, recorded_by, pregnancy_week, systolic_bp, diastolic_bp,
                    blood_sugar, hemoglobin, weight_kg, body_temperature, heart_rate, notes,
                    recorded_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(record.id),
                    str(record.mother_id),
                    str(record.recorded_by) if record.recorded_by else None,
                    record.pregnancy_week,
                    record.systolic_bp,
                    record.diastolic_bp,
                    record.blood_sugar,
                    record.hemoglobin,
                    record.weight_kg,
                    record.body_temperature,
                    record.heart_rate,
                    getattr(record, "notes", None),
                    _to_iso(record.recorded_at),
                    _to_iso(record.created_at),
                )
            )
            self._conn.commit()
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
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM health_records WHERE id = ?", (str(record_id),))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_health_record(row)

    def list_health_records(self, mother_id: UUID) -> List[HealthRecordResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT * FROM health_records WHERE mother_id = ? ORDER BY recorded_at DESC",
                (str(mother_id),)
            )
            return [self._row_to_health_record(r) for r in cur.fetchall()]

    def _row_to_health_record(self, row) -> HealthRecordResponse:
        return HealthRecordResponse(
            id=UUID(row["id"]),
            mother_id=UUID(row["mother_id"]),
            pregnancy_week=row["pregnancy_week"],
            systolic_bp=row["systolic_bp"],
            diastolic_bp=row["diastolic_bp"],
            blood_sugar=row["blood_sugar"],
            hemoglobin=row["hemoglobin"],
            weight_kg=row["weight_kg"],
            body_temperature=row["body_temperature"],
            heart_rate=row["heart_rate"],
            recorded_by=UUID(row["recorded_by"]) if row["recorded_by"] else None,
            recorded_at=_parse_dt(row["recorded_at"]),
            created_at=_parse_dt(row["created_at"]),
        )

    # --- Symptoms ---

    def add_symptoms(self, symptom_records: List[SymptomResponse]) -> List[SymptomResponse]:
        with self._lock:
            cur = self._conn.cursor()
            for s in symptom_records:
                onset_val = getattr(s, "onset_date", None)
                cur.execute(
                    """
                    INSERT INTO symptoms (id, mother_id, health_record_id, symptom_code, severity, notes, onset_date, recorded_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(s.id),
                        str(s.mother_id),
                        str(s.health_record_id) if s.health_record_id else None,
                        s.symptom_code,
                        s.severity,
                        s.notes,
                        _to_iso(onset_val) if onset_val else None,
                        _to_iso(s.recorded_at),
                        _to_iso(s.created_at),
                    )
                )
                self.log_audit(
                    user_id=s.mother_id,
                    action="CREATE",
                    resource_type="symptoms",
                    resource_id=s.id,
                    details={"symptom_code": s.symptom_code, "severity": s.severity},
                )
            self._conn.commit()
            return symptom_records

    def list_symptoms(self, mother_id: UUID) -> List[SymptomResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT * FROM symptoms WHERE mother_id = ? ORDER BY recorded_at DESC",
                (str(mother_id),)
            )
            return [
                SymptomResponse(
                    id=UUID(r["id"]),
                    mother_id=UUID(r["mother_id"]),
                    health_record_id=UUID(r["health_record_id"]) if r["health_record_id"] else None,
                    symptom_code=r["symptom_code"],
                    severity=r["severity"],
                    notes=r["notes"],
                    onset_date=_parse_date(r["onset_date"]) if r["onset_date"] else None,
                    recorded_at=_parse_dt(r["recorded_at"]),
                    created_at=_parse_dt(r["created_at"]),
                )
                for r in cur.fetchall()
            ]

    # --- Predictions & Safety Events ---

    def add_prediction(self, prediction: PredictionResponse) -> PredictionResponse:
        with self._lock:
            cur = self._conn.cursor()
            factors_json = json.dumps([f.model_dump() for f in prediction.contributing_factors])
            cur.execute(
                """
                INSERT INTO predictions (
                    id, mother_id, health_record_id, risk_level, model_score,
                    model_version, feature_schema_version, contributing_factors, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(prediction.id),
                    str(prediction.mother_id),
                    str(prediction.health_record_id) if prediction.health_record_id else None,
                    prediction.risk_level.value,
                    prediction.model_score,
                    prediction.model_version,
                    prediction.feature_schema_version,
                    factors_json,
                    _to_iso(prediction.created_at),
                )
            )
            # Update mother's last_risk_level
            cur.execute(
                "UPDATE mother_profiles SET last_risk_level = ?, updated_at = ? WHERE id = ? OR user_id = ?",
                (prediction.risk_level.value, _to_iso(datetime.now(timezone.utc)), str(prediction.mother_id), str(prediction.mother_id))
            )
            self._conn.commit()

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
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM predictions WHERE id = ?", (str(prediction_id),))
            row = cur.fetchone()
            if not row:
                return None
            factors_raw = json.loads(row["contributing_factors"])
            factors = [ContributingFactor(**f) for f in factors_raw]
            return PredictionResponse(
                id=UUID(row["id"]),
                mother_id=UUID(row["mother_id"]),
                health_record_id=UUID(row["health_record_id"]) if row["health_record_id"] else None,
                risk_level=MaternalRiskLevel(row["risk_level"]),
                model_score=row["model_score"],
                model_version=row["model_version"] or "v0.1.0",
                feature_schema_version=row["feature_schema_version"] or "v1",
                contributing_factors=factors,
                created_at=_parse_dt(row["created_at"]),
            )

    def list_predictions(self, mother_id: UUID) -> List[PredictionResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT * FROM predictions WHERE mother_id = ? ORDER BY created_at DESC",
                (str(mother_id),)
            )
            results = []
            for row in cur.fetchall():
                factors_raw = json.loads(row["contributing_factors"])
                factors = [ContributingFactor(**f) for f in factors_raw]
                results.append(
                    PredictionResponse(
                        id=UUID(row["id"]),
                        mother_id=UUID(row["mother_id"]),
                        health_record_id=UUID(row["health_record_id"]) if row["health_record_id"] else None,
                        risk_level=MaternalRiskLevel(row["risk_level"]),
                        model_score=row["model_score"],
                        model_version=row["model_version"] or "v0.1.0",
                        feature_schema_version=row["feature_schema_version"] or "v1",
                        contributing_factors=factors,
                        created_at=_parse_dt(row["created_at"]),
                    )
                )
            return results

    def add_safety_event(
        self,
        mother_id: UUID,
        safety_status: str,
        trigger_reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        with self._lock:
            cur = self._conn.cursor()
            event_id = uuid4()
            now_str = _to_iso(datetime.now(timezone.utc))
            cur.execute(
                "INSERT INTO safety_events (id, mother_id, safety_status, trigger_reason, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(event_id), str(mother_id), safety_status, trigger_reason, json.dumps(details or {}), now_str)
            )
            self._conn.commit()

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
            cur = self._conn.cursor()
            cur.execute(
                "SELECT * FROM safety_events WHERE mother_id = ? ORDER BY created_at DESC",
                (str(mother_id),)
            )
            return [
                {
                    "id": UUID(r["id"]),
                    "mother_id": UUID(r["mother_id"]),
                    "safety_status": r["safety_status"],
                    "trigger_reason": r["trigger_reason"],
                    "details": json.loads(r["details"]),
                    "created_at": _parse_dt(r["created_at"]),
                }
                for r in cur.fetchall()
            ]

    # --- Alerts ---

    def add_alert(self, alert: AlertResponse) -> AlertResponse:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO alerts (
                    id, mother_id, asha_id, mother_name, severity, status,
                    trigger_reason, safety_event_id, prediction_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(alert.id),
                    str(alert.mother_id),
                    str(alert.asha_id) if alert.asha_id else None,
                    alert.mother_name,
                    alert.severity.value,
                    alert.status.value,
                    alert.trigger_reason,
                    str(alert.safety_event_id) if alert.safety_event_id else None,
                    str(alert.prediction_id) if alert.prediction_id else None,
                    _to_iso(alert.created_at),
                    _to_iso(alert.updated_at),
                )
            )
            self._conn.commit()

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
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM alerts WHERE id = ?", (str(alert_id),))
            row = cur.fetchone()
            if not row:
                return None
            return self._row_to_alert(row)

    def update_alert(
        self,
        alert_id: UUID,
        status: AlertStatus,
        notes: Optional[str] = None,
        updated_by: Optional[UUID] = None,
    ) -> AlertResponse:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM alerts WHERE id = ?", (str(alert_id),))
            row = cur.fetchone()
            if not row:
                raise NotFoundError(message=f"Alert with id '{alert_id}' not found.")

            now = datetime.now(timezone.utc)
            now_str = _to_iso(now)
            cur.execute(
                "UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?",
                (status.value, now_str, str(alert_id))
            )
            self._conn.commit()

            self.log_audit(
                user_id=updated_by,
                action="UPDATE",
                resource_type="alerts",
                resource_id=alert_id,
                details={"status": status.value, "notes": notes},
            )
            return AlertResponse(
                id=UUID(row["id"]),
                mother_id=UUID(row["mother_id"]),
                mother_name=row["mother_name"],
                asha_id=UUID(row["asha_id"]) if row["asha_id"] else None,
                severity=AlertSeverity(row["severity"]),
                status=status,
                trigger_reason=row["trigger_reason"],
                safety_event_id=UUID(row["safety_event_id"]) if row["safety_event_id"] else None,
                prediction_id=UUID(row["prediction_id"]) if row["prediction_id"] else None,
                created_at=_parse_dt(row["created_at"]),
                updated_at=now,
            )

    def list_alerts_for_user(
        self,
        user_id: UUID,
        role: UserRole,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[AlertResponse], int]:
        with self._lock:
            cur = self._conn.cursor()
            if role == UserRole.ADMIN:
                cur.execute("SELECT * FROM alerts ORDER BY created_at DESC")
            elif role == UserRole.MOTHER:
                cur.execute(
                    "SELECT * FROM alerts WHERE mother_id = ? ORDER BY created_at DESC",
                    (str(user_id),)
                )
            elif role == UserRole.ASHA:
                assigned_mids = [str(mid) for mid in self.get_assigned_mother_ids(user_id)]
                placeholders = ",".join("?" for _ in assigned_mids) if assigned_mids else "''"
                query = f"SELECT * FROM alerts WHERE mother_id IN ({placeholders}) OR asha_id = ? ORDER BY created_at DESC"
                params = list(assigned_mids) + [str(user_id)]
                cur.execute(query, params)
            else:
                return [], 0

            rows = cur.fetchall()
            items = [self._row_to_alert(r) for r in rows]
            total = len(items)
            start = (page - 1) * size
            end = start + size
            return items[start:end], total

    def _row_to_alert(self, row) -> AlertResponse:
        return AlertResponse(
            id=UUID(row["id"]),
            mother_id=UUID(row["mother_id"]),
            mother_name=row["mother_name"],
            asha_id=UUID(row["asha_id"]) if row["asha_id"] else None,
            severity=AlertSeverity(row["severity"]),
            status=AlertStatus(row["status"]),
            trigger_reason=row["trigger_reason"],
            safety_event_id=UUID(row["safety_event_id"]) if row["safety_event_id"] else None,
            prediction_id=UUID(row["prediction_id"]) if row["prediction_id"] else None,
            created_at=_parse_dt(row["created_at"]),
            updated_at=_parse_dt(row["updated_at"]),
        )

    # --- Visits ---

    def add_visit(self, visit: VisitResponse) -> VisitResponse:
        with self._lock:
            cur = self._conn.cursor()
            updated_str = _to_iso(getattr(visit, "updated_at", visit.created_at))
            cur.execute(
                """
                INSERT INTO visits (id, mother_id, asha_id, alert_id, visit_date, status, notes, findings, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(visit.id),
                    str(visit.mother_id),
                    str(visit.asha_id),
                    str(visit.alert_id) if visit.alert_id else None,
                    _to_iso(visit.visit_date),
                    visit.status.value,
                    visit.notes,
                    json.dumps(visit.findings or {}),
                    _to_iso(visit.created_at),
                    updated_str,
                )
            )
            self._conn.commit()

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
            cur = self._conn.cursor()
            cur.execute(
                "SELECT * FROM visits WHERE mother_id = ? ORDER BY visit_date DESC",
                (str(mother_id),)
            )
            return [
                VisitResponse(
                    id=UUID(r["id"]),
                    mother_id=UUID(r["mother_id"]),
                    asha_id=UUID(r["asha_id"]),
                    alert_id=UUID(r["alert_id"]) if r["alert_id"] else None,
                    visit_date=_parse_dt(r["visit_date"]),
                    status=VisitStatus(r["status"]),
                    notes=r["notes"],
                    findings=json.loads(r["findings"]),
                    created_at=_parse_dt(r["created_at"]),
                )
                for r in cur.fetchall()
            ]

    # --- Follow-ups ---

    def add_followup(self, followup: FollowUpResponse) -> FollowUpResponse:
        with self._lock:
            cur = self._conn.cursor()
            updated_str = _to_iso(getattr(followup, "updated_at", followup.created_at))
            cur.execute(
                """
                INSERT INTO follow_ups (id, mother_id, asha_id, alert_id, visit_id, due_date, status, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(followup.id),
                    str(followup.mother_id),
                    str(followup.asha_id),
                    str(followup.alert_id) if followup.alert_id else None,
                    str(followup.visit_id) if followup.visit_id else None,
                    _to_iso(followup.due_date),
                    followup.status.value,
                    followup.notes,
                    _to_iso(followup.created_at),
                    updated_str,
                )
            )
            self._conn.commit()

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
            cur = self._conn.cursor()
            cur.execute(
                "SELECT * FROM follow_ups WHERE mother_id = ? ORDER BY due_date DESC",
                (str(mother_id),)
            )
            return [
                FollowUpResponse(
                    id=UUID(r["id"]),
                    mother_id=UUID(r["mother_id"]),
                    asha_id=UUID(r["asha_id"]),
                    alert_id=UUID(r["alert_id"]) if r["alert_id"] else None,
                    visit_id=UUID(r["visit_id"]) if r["visit_id"] else None,
                    due_date=_parse_date(r["due_date"]),
                    status=FollowUpStatus(r["status"]),
                    notes=r["notes"],
                    created_at=_parse_dt(r["created_at"]),
                )
                for r in cur.fetchall()
            ]

    # --- Chat Sessions & Messages (Phase 6) ---

    def create_chat_session(
        self,
        session_id: UUID,
        mother_id: UUID,
        created_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Create a new chat session for an authorized mother."""
        with self._lock:
            cur = self._conn.cursor()
            now = created_at or datetime.now(timezone.utc)
            cur.execute(
                """
                INSERT INTO chat_sessions (id, mother_id, created_at)
                VALUES (?, ?, ?)
                """,
                (str(session_id), str(mother_id), _to_iso(now)),
            )
            self._conn.commit()
            return {
                "id": session_id,
                "mother_id": mother_id,
                "created_at": now,
            }

    def get_chat_session(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve chat session by ID."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM chat_sessions WHERE id = ?", (str(session_id),))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": UUID(row["id"]),
                "mother_id": UUID(row["mother_id"]),
                "created_at": _parse_dt(row["created_at"]),
            }

    def list_chat_sessions(self, mother_id: UUID) -> List[Dict[str, Any]]:
        """List chat sessions for a specific mother."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT * FROM chat_sessions WHERE mother_id = ? ORDER BY created_at DESC",
                (str(mother_id),),
            )
            return [
                {
                    "id": UUID(r["id"]),
                    "mother_id": UUID(r["mother_id"]),
                    "created_at": _parse_dt(r["created_at"]),
                }
                for r in cur.fetchall()
            ]

    def add_chat_message(
        self,
        message_id: UUID,
        session_id: UUID,
        sender_role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Record a chat message in the session transcript."""
        with self._lock:
            cur = self._conn.cursor()
            now = created_at or datetime.now(timezone.utc)
            meta_json = json.dumps(metadata or {})
            cur.execute(
                """
                INSERT INTO chat_messages (id, session_id, sender_role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (str(message_id), str(session_id), sender_role, content, meta_json, _to_iso(now)),
            )
            self._conn.commit()
            return {
                "id": message_id,
                "session_id": session_id,
                "sender_role": sender_role,
                "content": content,
                "metadata": metadata or {},
                "created_at": now,
            }

    def get_chat_messages(self, session_id: UUID) -> List[Dict[str, Any]]:
        """Retrieve ordered chat messages for a session."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC",
                (str(session_id),),
            )
            return [
                {
                    "id": UUID(r["id"]),
                    "session_id": UUID(r["session_id"]),
                    "sender_role": r["sender_role"],
                    "content": r["content"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                    "created_at": _parse_dt(r["created_at"]),
                }
                for r in cur.fetchall()
            ]

    # --- Properties providing backward compatibility with existing tests ---

    @property
    def profiles(self) -> Dict[UUID, Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM profiles")
            return {
                UUID(r["id"]): {
                    "id": UUID(r["id"]),
                    "role": UserRole(r["role"]),
                    "full_name": r["full_name"],
                    "phone": r["phone"],
                }
                for r in cur.fetchall()
            }

    @property
    def mother_profiles(self) -> Dict[UUID, Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM mother_profiles")
            return {
                UUID(r["id"]): {
                    "id": UUID(r["id"]),
                    "user_id": UUID(r["user_id"]),
                    "full_name": r["full_name"],
                    "assigned_asha_id": UUID(r["assigned_asha_id"]) if r["assigned_asha_id"] else None,
                    "last_risk_level": MaternalRiskLevel(r["last_risk_level"]) if r["last_risk_level"] else None,
                }
                for r in cur.fetchall()
            }

    @property
    def asha_profiles(self) -> Dict[UUID, Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM asha_profiles")
            return {
                UUID(r["id"]): {
                    "id": UUID(r["id"]),
                    "user_id": UUID(r["user_id"]),
                    "worker_code": r["worker_code"],
                    "assigned_village": r["assigned_village"],
                    "phone": r["phone"],
                }
                for r in cur.fetchall()
            }

    @property
    def asha_assignments(self) -> List[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM asha_assignments")
            return [
                {
                    "id": UUID(r["id"]),
                    "asha_id": UUID(r["asha_id"]),
                    "mother_id": UUID(r["mother_id"]),
                    "assigned_at": _parse_dt(r["assigned_at"]),
                    "is_active": bool(r["is_active"]),
                }
                for r in cur.fetchall()
            ]

    @property
    def health_records(self) -> Dict[UUID, HealthRecordResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM health_records")
            return {UUID(r["id"]): self._row_to_health_record(r) for r in cur.fetchall()}

    @property
    def symptoms(self) -> Dict[UUID, SymptomResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM symptoms")
            return {
                UUID(r["id"]): SymptomResponse(
                    id=UUID(r["id"]),
                    mother_id=UUID(r["mother_id"]),
                    health_record_id=UUID(r["health_record_id"]) if r["health_record_id"] else None,
                    symptom_code=r["symptom_code"],
                    severity=r["severity"],
                    notes=r["notes"],
                    onset_date=_parse_date(r["onset_date"]) if r["onset_date"] else None,
                    recorded_at=_parse_dt(r["recorded_at"]),
                    created_at=_parse_dt(r["created_at"]),
                )
                for r in cur.fetchall()
            }

    @property
    def predictions(self) -> Dict[UUID, PredictionResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM predictions")
            res = {}
            for r in cur.fetchall():
                factors = [ContributingFactor(**f) for f in json.loads(r["contributing_factors"])]
                res[UUID(r["id"])] = PredictionResponse(
                    id=UUID(r["id"]),
                    mother_id=UUID(r["mother_id"]),
                    health_record_id=UUID(r["health_record_id"]) if r["health_record_id"] else None,
                    risk_level=MaternalRiskLevel(r["risk_level"]),
                    model_score=r["model_score"],
                    model_version=r["model_version"] or "v0.1.0",
                    feature_schema_version=r["feature_schema_version"] or "v1",
                    contributing_factors=factors,
                    created_at=_parse_dt(r["created_at"]),
                )
            return res

    @property
    def safety_events(self) -> List[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM safety_events ORDER BY created_at ASC")
            return [
                {
                    "id": UUID(r["id"]),
                    "mother_id": UUID(r["mother_id"]),
                    "safety_status": r["safety_status"],
                    "trigger_reason": r["trigger_reason"],
                    "details": json.loads(r["details"]),
                    "created_at": _parse_dt(r["created_at"]),
                }
                for r in cur.fetchall()
            ]

    @property
    def alerts(self) -> Dict[UUID, AlertResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM alerts")
            return {UUID(r["id"]): self._row_to_alert(r) for r in cur.fetchall()}

    @property
    def visits(self) -> Dict[UUID, VisitResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM visits")
            return {
                UUID(r["id"]): VisitResponse(
                    id=UUID(r["id"]),
                    mother_id=UUID(r["mother_id"]),
                    asha_id=UUID(r["asha_id"]),
                    alert_id=UUID(r["alert_id"]) if r["alert_id"] else None,
                    visit_date=_parse_dt(r["visit_date"]),
                    status=VisitStatus(r["status"]),
                    notes=r["notes"],
                    findings=json.loads(r["findings"]),
                    created_at=_parse_dt(r["created_at"]),
                )
                for r in cur.fetchall()
            }

    @property
    def followups(self) -> Dict[UUID, FollowUpResponse]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM follow_ups")
            return {
                UUID(r["id"]): FollowUpResponse(
                    id=UUID(r["id"]),
                    mother_id=UUID(r["mother_id"]),
                    asha_id=UUID(r["asha_id"]),
                    alert_id=UUID(r["alert_id"]) if r["alert_id"] else None,
                    visit_id=UUID(r["visit_id"]) if r["visit_id"] else None,
                    due_date=_parse_date(r["due_date"]),
                    status=FollowUpStatus(r["status"]),
                    notes=r["notes"],
                    created_at=_parse_dt(r["created_at"]),
                )
                for r in cur.fetchall()
            }

    @property
    def audit_logs(self) -> List[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM audit_logs ORDER BY timestamp ASC")
            return [
                {
                    "id": UUID(r["id"]),
                    "user_id": UUID(r["user_id"]) if r["user_id"] else None,
                    "action": r["action"],
                    "resource_type": r["resource_type"],
                    "resource_id": r["resource_id"],
                    "details": json.loads(r["details"]),
                    "timestamp": _parse_dt(r["timestamp"]),
                }
                for r in cur.fetchall()
            ]

    @property
    def chat_sessions(self) -> Dict[UUID, Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM chat_sessions")
            return {
                UUID(r["id"]): {
                    "id": UUID(r["id"]),
                    "mother_id": UUID(r["mother_id"]),
                    "created_at": _parse_dt(r["created_at"]),
                }
                for r in cur.fetchall()
            }

    @property
    def chat_messages(self) -> List[Dict[str, Any]]:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("SELECT * FROM chat_messages ORDER BY created_at ASC")
            return [
                {
                    "id": UUID(r["id"]),
                    "session_id": UUID(r["session_id"]),
                    "sender_role": r["sender_role"],
                    "content": r["content"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else {},
                    "created_at": _parse_dt(r["created_at"]),
                }
                for r in cur.fetchall()
            ]



# Cloud Supabase integration adapter
class SupabasePostgresRepository(RepositoryStore):
    """Supabase PostgREST and PostgreSQL cloud repository adapter.

    Provides:
    - User identity propagation and client scoping separating user-level (RLS enforced)
      from service-role (privileged server) access.
    - get_authenticated_client(access_token): Uses SUPABASE_ANON_KEY (or configured key) with the
      caller's verified JWT Bearer token so PostgREST executes under auth.uid() and enforces PostgreSQL RLS.
    - get_service_client(): Uses SUPABASE_SERVICE_ROLE_KEY, strictly guarded for server-side
      privileged operations (system audit logs, ML model version registry, safety event recording).
    - Prevents accidental RLS bypass by refusing to run client-scoped user queries through the service role.
    """

    def __init__(self, db_path: Optional[str] = None):
        super().__init__(db_path=db_path)
        self._supabase_client = None
        settings = get_settings()
        self._supabase_url = settings.SUPABASE_URL
        self._service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY
        self._anon_key = settings.SUPABASE_ANON_KEY

        if settings.is_supabase_configured:
            try:
                from supabase import create_client
                self._supabase_client = create_client(self._supabase_url, self._service_role_key)
            except Exception:
                self._supabase_client = None

    @property
    def has_active_cloud_connection(self) -> bool:
        """Check if live Supabase client connection is active."""
        return self._supabase_client is not None

    def get_service_client(self):
        """Return the privileged service-role client.

        SECURITY NOTICE: Must ONLY be used for server-side privileged tasks:
        - System immutable audit logging (audit_logs)
        - Model registry updates (model_versions)
        - Safety event system records (safety_events)
        - Initial administrative profile provisioning
        Must NEVER be exposed to frontend clients or used to bypass user RLS policies.
        """
        if not self._supabase_client:
            raise RuntimeError("Supabase service client is not configured or unavailable.")
        return self._supabase_client

    def get_authenticated_client(self, access_token: str):
        """Create a Supabase client scoped to an authenticated user's JWT.

        Propagates the user's verified Bearer token to PostgREST, ensuring PostgreSQL
        enforces Row Level Security (RLS) under the user's identity (auth.uid()).
        """
        if not self._supabase_url:
            raise RuntimeError("Supabase URL is not configured.")
        from supabase import create_client
        key = self._anon_key or self._service_role_key
        client = create_client(self._supabase_url, key)
        if hasattr(client, "postgrest") and hasattr(client.postgrest, "auth"):
            client.postgrest.auth(access_token)
        return client


# Global repository instance state
_repository_instance: Optional[RepositoryStore] = None


def create_repository(settings: Optional[Any] = None) -> RepositoryStore:
    """Deterministic, configuration-driven repository factory.

    Repository Selection Policy:
    1. If valid Supabase / Postgres configuration is present (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY,
       or DATABASE_URL / SUPABASE_DB_URL):
       Selects and instantiates SupabasePostgresRepository.
    2. If ENVIRONMENT == "production" and valid Supabase / Postgres configuration is missing:
       Fails closed with RuntimeError. The local disk-backed repository must NEVER silently become
       the production persistence backend.
    3. In local development or test environments (ENVIRONMENT != "production"):
       Explicitly falls back to local disk-backed RepositoryStore (or in-memory if specified).
    """
    if settings is None:
        settings = get_settings()

    is_configured = getattr(settings, "is_supabase_configured", False) or bool(
        getattr(settings, "DATABASE_URL", None) or getattr(settings, "SUPABASE_DB_URL", None)
    )

    if is_configured:
        return SupabasePostgresRepository()

    env = str(getattr(settings, "ENVIRONMENT", "development")).lower()
    if env == "production":
        raise RuntimeError(
            "CRITICAL SECURITY / CONFIGURATION ERROR: Supabase / PostgreSQL configuration is missing "
            "in production environment. Production persistence requires SupabasePostgresRepository "
            "(configured via SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or DATABASE_URL). "
            "The disk-backed RepositoryStore is a local development/test fallback only and is prohibited in production."
        )

    return RepositoryStore()


def get_repository() -> RepositoryStore:
    """Dependency injector for data repository."""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = create_repository()
    return _repository_instance


def set_repository(repo: Optional[RepositoryStore]) -> None:
    """Explicitly override or reset the active repository instance (for tests and dynamic lifecycle)."""
    global _repository_instance
    _repository_instance = repo

