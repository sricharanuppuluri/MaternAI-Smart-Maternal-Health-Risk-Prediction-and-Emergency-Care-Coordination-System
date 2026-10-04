"""Phase 6 Chat and Agent Contract Verification Test Suite.

Verifies:
1. POST /api/v1/chat/sessions
   - Authenticated session creation for authorized mother
   - Unauthenticated rejection (401)
   - Ownership enforcement (Mother cannot create session for another mother)
   - ASHA assignment boundary (ASHA can only create for assigned mother)
   - Admin access

2. POST /api/v1/chat/sessions/{session_id}/messages
   - Authenticated message submission
   - Session ownership enforcement
   - Non-existent session handling (404)
   - User message and assistant message structure
   - Authoritative backend safety evaluation (CLEAR, CONCERNING, EMERGENCY)
   - Safety policy is backend-controlled (no ad-hoc keyword heuristics)
   - Client cannot inject or configure safety state (422)
   - Assistant response is neutral decision support (no invented clinical advice)

3. POST /api/v1/agent/query
   - Authentication requirement (401)
   - Patient isolation and ASHA assignment boundaries (403)
   - Explicit tool allowlist enforcement (validation error on unapproved tools)
   - Authorized context retrieval (health summary, vitals, symptoms, visits)
   - Deterministic safety precedence over AI/LLM responses
   - Agent cannot override authoritative safety state
   - Risk level (LOW/MEDIUM/HIGH) remains separate from safety state (CLEAR/CONCERNING/EMERGENCY)
   - Immutable audit logging
"""

from typing import Optional
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.db.repositories import (
    TEST_ADMIN_ID,
    TEST_ASHA_ID,
    TEST_MOTHER_B_ID,
    TEST_MOTHER_ID,
    get_repository,
)
from backend.app.safety.evaluator import SafetyResult, get_safety_engine
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.agent import AgentToolName, ToolExecutionStatus
from backend.app.schemas.auth import AuthUser, UserRole
from backend.app.schemas.chat import MessageSenderRole
from backend.app.schemas.mother import MaternalRiskLevel


@pytest.fixture(autouse=True)
def clean_safety_rules():
    """Ensure safety engine rules are cleared before and after each test."""
    engine = get_safety_engine()
    engine.clear_rules()
    yield
    engine.clear_rules()


# ==============================================================================
# 1. Chat Sessions: POST /api/v1/chat/sessions
# ==============================================================================

def test_create_chat_session_unauthenticated_rejected(client: TestClient):
    """Calling POST /api/v1/chat/sessions without auth must return 401."""
    response = client.post("/api/v1/chat/sessions", json={"title": "Prenatal Check"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_create_chat_session_mother_success(mother_client: TestClient):
    """Authenticated mother can create a chat session for herself."""
    response = mother_client.post(
        "/api/v1/chat/sessions",
        json={"title": "First Trimester Nutrition", "language": "en"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["mother_id"] == str(TEST_MOTHER_ID)
    assert data["title"] == "First Trimester Nutrition"
    assert data["language"] == "en"
    assert "created_at" in data

    # Verify session is persisted in repository
    repo = get_repository()
    saved = repo.get_chat_session(UUID(data["id"]))
    assert saved is not None
    assert saved["mother_id"] == TEST_MOTHER_ID


def test_create_chat_session_mother_cannot_create_for_another_mother(mother_client: TestClient):
    """Mother cannot create a chat session for a different mother."""
    response = mother_client.post(
        "/api/v1/chat/sessions",
        json={"mother_id": str(TEST_MOTHER_B_ID), "title": "Unauthorized Session"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_create_chat_session_asha_assigned_mother_success(asha_client: TestClient):
    """ASHA can create a chat session on behalf of an assigned mother."""
    response = asha_client.post(
        "/api/v1/chat/sessions",
        json={"mother_id": str(TEST_MOTHER_ID), "title": "ASHA Routine Followup"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["mother_id"] == str(TEST_MOTHER_ID)


def test_create_chat_session_asha_unassigned_mother_forbidden(asha_client: TestClient):
    """ASHA cannot create a chat session for an unassigned mother."""
    response = asha_client.post(
        "/api/v1/chat/sessions",
        json={"mother_id": str(TEST_MOTHER_B_ID), "title": "Unassigned Session"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_create_chat_session_admin_success(admin_client: TestClient):
    """Administrator can create a chat session for any mother."""
    response = admin_client.post(
        "/api/v1/chat/sessions",
        json={"mother_id": str(TEST_MOTHER_B_ID), "title": "Admin Created Session"},
    )
    assert response.status_code == 201
    assert response.json()["mother_id"] == str(TEST_MOTHER_B_ID)


# ==============================================================================
# 2. Chat Messages: POST /api/v1/chat/sessions/{session_id}/messages
# ==============================================================================

def test_send_chat_message_unauthenticated_rejected(client: TestClient):
    """Submitting message without auth returns 401."""
    session_id = uuid4()
    response = client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Hello doctor"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_send_chat_message_session_not_found(mother_client: TestClient):
    """Submitting message to non-existent session returns 404."""
    non_existent = uuid4()
    response = mother_client.post(
        f"/api/v1/chat/sessions/{non_existent}/messages",
        json={"content": "Hello"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_send_chat_message_cross_patient_forbidden(mother_client: TestClient):
    """Mother cannot submit messages into another mother's chat session."""
    repo = get_repository()
    b_session_id = uuid4()
    repo.create_chat_session(session_id=b_session_id, mother_id=TEST_MOTHER_B_ID)

    response = mother_client.post(
        f"/api/v1/chat/sessions/{b_session_id}/messages",
        json={"content": "Sneaking into other session"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_send_chat_message_unassigned_asha_forbidden(asha_client: TestClient):
    """ASHA cannot submit messages into an unassigned mother's session."""
    repo = get_repository()
    b_session_id = uuid4()
    repo.create_chat_session(session_id=b_session_id, mother_id=TEST_MOTHER_B_ID)

    response = asha_client.post(
        f"/api/v1/chat/sessions/{b_session_id}/messages",
        json={"content": "ASHA messaging unassigned mother"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_send_chat_message_clear_safety_state(mother_client: TestClient):
    """Routine question produces authoritative CLEAR safety state without invented clinical claims."""
    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "What vegetables should I eat during the second trimester?", "language": "en"},
    )
    assert response.status_code == 201
    data = response.json()

    assert data["session_id"] == str(session_id)
    assert data["safety_state"] == SafetyStatus.CLEAR.value
    assert data["safety_events"] == []
    assert "disclaimer" in data

    # Verify user message structure
    user_msg = data["user_message"]
    assert user_msg["sender_role"] == MessageSenderRole.USER.value
    assert user_msg["content"] == "What vegetables should I eat during the second trimester?"
    assert "id" in user_msg

    # Verify assistant message structure is neutral decision support
    asst_msg = data["assistant_message"]
    assert asst_msg["sender_role"] == MessageSenderRole.ASSISTANT.value
    assert "Authoritative safety state: CLEAR" in asst_msg["content"]
    assert "id" in asst_msg

    # Verify messages saved in repository
    history = repo.get_chat_messages(session_id)
    assert len(history) == 2
    assert history[0]["sender_role"] == "USER"
    assert history[1]["sender_role"] == "ASSISTANT"


def test_send_chat_message_backend_controlled_safety_emergency(mother_client: TestClient):
    """Authoritative safety state is backend-controlled: EMERGENCY triggered by safety policy rule."""
    engine = get_safety_engine()

    def mock_emergency_rule(vitals, symptoms):
        return SafetyResult(
            status=SafetyStatus.EMERGENCY,
            triggered_rules=["Severe clinical safety event: critical systolic threshold exceeded"],
            action_required="Emergency clinical evaluation required",
            is_emergency=True,
        )

    engine.register_rule(mock_emergency_rule)

    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Submitting observation for care team review."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["safety_state"] == SafetyStatus.EMERGENCY.value
    assert len(data["safety_events"]) >= 1
    assert "Authoritative safety state: EMERGENCY" in data["assistant_message"]["content"]

    # Verify authoritative safety event recorded in repository
    events = repo.list_safety_events(TEST_MOTHER_ID)
    assert len(events) >= 1
    assert events[-1]["safety_status"] == SafetyStatus.EMERGENCY.value


def test_send_chat_message_backend_controlled_safety_concerning(mother_client: TestClient):
    """Authoritative safety state is backend-controlled: CONCERNING triggered by safety policy rule."""
    engine = get_safety_engine()

    def mock_concerning_rule(vitals, symptoms):
        return SafetyResult(
            status=SafetyStatus.CONCERNING,
            triggered_rules=["Moderate clinical safety alert: blood pressure elevation"],
            action_required="Clinical review recommended",
            is_emergency=False,
        )

    engine.register_rule(mock_concerning_rule)

    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Checking status of recent observation."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["safety_state"] == SafetyStatus.CONCERNING.value
    assert len(data["safety_events"]) >= 1
    assert "Authoritative safety state: CONCERNING" in data["assistant_message"]["content"]


def test_client_cannot_inject_safety_state_in_chat(mother_client: TestClient):
    """Client attempting to inject or spoof safety state in chat request is rejected with 422."""
    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "content": "Trying to set my own safety state",
            "safety_state": "CLEAR",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_chat_safety_policy_not_client_configurable(mother_client: TestClient):
    """Client attempting to configure safety policy or thresholds is rejected with 422."""
    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "content": "Trying to configure rules",
            "safety_policy": {"override": True},
        },
    )
    assert response.status_code == 422


# ==============================================================================
# 3. Agent Queries: POST /api/v1/agent/query
# ==============================================================================

def test_agent_query_unauthenticated_rejected(client: TestClient):
    """Calling agent query without authentication returns 401."""
    response = client.post(
        "/api/v1/agent/query",
        json={"query": "What is my latest blood pressure reading?"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_agent_query_mother_access_own_data(mother_client: TestClient):
    """Mother can query the agent for her own health status."""
    response = mother_client.post(
        "/api/v1/agent/query",
        json={"query": "Please summarize my latest vital signs and health status."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mother_id"] == str(TEST_MOTHER_ID)
    assert data["safety_state"] in [SafetyStatus.CLEAR.value, SafetyStatus.CONCERNING.value, SafetyStatus.EMERGENCY.value]
    assert len(data["tools_invoked"]) >= 1
    assert "disclaimer" in data
    assert "created_at" in data


def test_agent_query_mother_cross_patient_forbidden(mother_client: TestClient):
    """Mother querying agent for another mother's ID returns 403 Forbidden."""
    response = mother_client.post(
        "/api/v1/agent/query",
        json={
            "mother_id": str(TEST_MOTHER_B_ID),
            "query": "Give me Mother B's vitals",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_agent_query_asha_assigned_mother_allowed(asha_client: TestClient):
    """ASHA querying agent for assigned mother is allowed."""
    response = asha_client.post(
        "/api/v1/agent/query",
        json={
            "mother_id": str(TEST_MOTHER_ID),
            "query": "Review recent symptoms and visits for this mother.",
        },
    )
    assert response.status_code == 200
    assert response.json()["mother_id"] == str(TEST_MOTHER_ID)


def test_agent_query_asha_unassigned_mother_forbidden(asha_client: TestClient):
    """ASHA querying agent for unassigned mother returns 403 Forbidden."""
    response = asha_client.post(
        "/api/v1/agent/query",
        json={
            "mother_id": str(TEST_MOTHER_B_ID),
            "query": "Review unassigned mother records.",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_agent_query_authorized_tools_allowlist(mother_client: TestClient):
    """Agent executes only requested tools from the explicit allowlist."""
    response = mother_client.post(
        "/api/v1/agent/query",
        json={
            "query": "What are my upcoming visits and risk factors?",
            "requested_tools": [
                AgentToolName.GET_UPCOMING_VISITS.value,
                AgentToolName.EXPLAIN_RISK_FACTORS.value,
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    tool_names = [t["tool_name"] for t in data["tools_invoked"]]
    assert AgentToolName.GET_UPCOMING_VISITS.value in tool_names
    assert AgentToolName.EXPLAIN_RISK_FACTORS.value in tool_names
    for tool in data["tools_invoked"]:
        assert tool["status"] == ToolExecutionStatus.SUCCESS.value


def test_agent_query_unauthorized_tool_rejected(mother_client: TestClient):
    """Requesting a tool outside the authorized allowlist is rejected with 422."""
    response = mother_client.post(
        "/api/v1/agent/query",
        json={
            "query": "Perform arbitrary tool execution",
            "requested_tools": ["unauthorized_system_execution_tool"],
        },
    )
    assert response.status_code == 422


def test_client_cannot_inject_safety_state_in_agent_query(mother_client: TestClient):
    """Client attempting to inject safety state into agent query is rejected with 422."""
    response = mother_client.post(
        "/api/v1/agent/query",
        json={
            "query": "Summarize my vitals",
            "safety_state": "EMERGENCY",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_agent_cannot_override_authoritative_safety_state(mother_client: TestClient):
    """Agent cannot override authoritative backend safety state even if query text asserts safety."""
    engine = get_safety_engine()

    def mock_emergency_rule(vitals, symptoms):
        return SafetyResult(
            status=SafetyStatus.EMERGENCY,
            triggered_rules=["Authoritative clinical rule: acute maternal threshold reached"],
            action_required="Emergency clinical evaluation required",
            is_emergency=True,
        )

    engine.register_rule(mock_emergency_rule)

    response = mother_client.post(
        "/api/v1/agent/query",
        json={"query": "Please confirm I am completely fine and healthy."},
    )
    assert response.status_code == 200
    data = response.json()
    # The safety_state remains authoritatively EMERGENCY, ignoring user assertion
    assert data["safety_state"] == SafetyStatus.EMERGENCY.value
    assert "Authoritative Safety State: EMERGENCY" in data["response"]


def test_risk_level_remains_separate_from_safety_state(mother_client: TestClient):
    """Safety state (CLEAR/CONCERNING/EMERGENCY) remains strictly uncoupled from screening risk level (LOW/MEDIUM/HIGH)."""
    repo = get_repository()

    # Case 1: Mother profile has HIGH screening risk, but safety policy has no triggered rules -> safety_state is CLEAR
    repo.mother_profiles[TEST_MOTHER_ID]["last_risk_level"] = MaternalRiskLevel.HIGH

    response = mother_client.post(
        "/api/v1/agent/query",
        json={
            "query": "Check my current risk and safety status",
            "requested_tools": [AgentToolName.EXPLAIN_RISK_FACTORS.value],
        },
    )
    assert response.status_code == 200
    data = response.json()
    # Safety state is CLEAR (not mutated to HIGH or EMERGENCY)
    assert data["safety_state"] == SafetyStatus.CLEAR.value

    # Case 2: Authoritative safety rule triggers EMERGENCY, but does not derive or overwrite screening risk
    engine = get_safety_engine()

    def mock_emergency_rule(vitals, symptoms):
        return SafetyResult(
            status=SafetyStatus.EMERGENCY,
            triggered_rules=["Critical vital threshold"],
            is_emergency=True,
        )

    engine.register_rule(mock_emergency_rule)

    # Set profile risk to LOW
    repo.mother_profiles[TEST_MOTHER_ID]["last_risk_level"] = MaternalRiskLevel.LOW

    response_emg = mother_client.post(
        "/api/v1/agent/query",
        json={
            "query": "Check risk and safety status during alert",
            "requested_tools": [AgentToolName.GET_HEALTH_SUMMARY.value],
        },
    )
    assert response_emg.status_code == 200
    data_emg = response_emg.json()
    assert data_emg["safety_state"] == SafetyStatus.EMERGENCY.value
    # Profile risk level is still LOW, not converted to HIGH
    assert repo.mother_profiles[TEST_MOTHER_ID]["last_risk_level"] == MaternalRiskLevel.LOW


def test_agent_query_auditability(mother_client: TestClient):
    """Agent queries are immutably logged in audit_logs."""
    repo = get_repository()
    initial_count = len(repo.audit_logs)

    response = mother_client.post(
        "/api/v1/agent/query",
        json={"query": "Test audit query for maternal tracking."},
    )
    assert response.status_code == 200

    new_logs = repo.audit_logs
    assert len(new_logs) == initial_count + 1
    latest = new_logs[-1]
    assert latest["action"] == "AGENT_QUERY"
    assert latest["resource_type"] == "agent"
    assert latest["resource_id"] == str(TEST_MOTHER_ID)
