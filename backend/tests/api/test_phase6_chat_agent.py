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
   - Authoritative deterministic safety evaluation (CLEAR, CONCERNING, EMERGENCY)
   - Inability of client to override or manipulate safety state

3. POST /api/v1/agent/query
   - Authentication requirement (401)
   - Patient isolation and ASHA assignment boundaries (403)
   - Explicit tool allowlist enforcement (validation error on unapproved tools)
   - Authorized context retrieval (health summary, vitals, symptoms, visits)
   - Deterministic safety precedence over AI/LLM responses
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
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.agent import AgentToolName, ToolExecutionStatus
from backend.app.schemas.auth import AuthUser, UserRole
from backend.app.schemas.chat import MessageSenderRole


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
    # Create session owned by Mother B
    b_session_id = uuid4()
    repo.create_chat_session(session_id=b_session_id, mother_id=TEST_MOTHER_B_ID)

    # Mother A tries to post to Mother B's session
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
    """Routine question produces authoritative CLEAR safety state and assistant response."""
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

    # Verify assistant message structure
    asst_msg = data["assistant_message"]
    assert asst_msg["sender_role"] == MessageSenderRole.ASSISTANT.value
    assert "Maternal Care Guidance" in asst_msg["content"]
    assert "id" in asst_msg

    # Verify messages saved in repository
    history = repo.get_chat_messages(session_id)
    assert len(history) == 2
    assert history[0]["sender_role"] == "USER"
    assert history[1]["sender_role"] == "ASSISTANT"


def test_send_chat_message_concerning_safety_state(mother_client: TestClient):
    """Message describing concerning symptoms returns authoritative CONCERNING safety state."""
    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "I have had a mild fever and persistent dizziness since yesterday."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["safety_state"] == SafetyStatus.CONCERNING.value
    assert len(data["safety_events"]) >= 1
    assert "CONCERNING SYMPTOM NOTICE" in data["assistant_message"]["content"]


def test_send_chat_message_emergency_safety_state(mother_client: TestClient):
    """Message describing acute emergency red flags returns authoritative EMERGENCY safety state."""
    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Help me, I am experiencing severe vaginal bleeding and intense chest pain."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["safety_state"] == SafetyStatus.EMERGENCY.value
    assert any("bleeding" in e.lower() for e in data["safety_events"])
    assert "EMERGENCY ADVISORY" in data["assistant_message"]["content"]

    # Verify authoritative safety event recorded in repository
    events = repo.list_safety_events(TEST_MOTHER_ID)
    assert len(events) >= 1
    assert events[-1]["safety_status"] == SafetyStatus.EMERGENCY.value



def test_client_cannot_override_authoritative_safety_state(mother_client: TestClient):
    """Client attempting to inject or spoof safety state in request is rejected or ignored."""
    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    # 1. Extra fields are rejected by Pydantic model_config(extra='forbid')
    res_tamper = mother_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={
            "content": "I am experiencing severe bleeding",
            "safety_state": "CLEAR",  # Client attempts to spoof CLEAR on an emergency
        },
    )
    assert res_tamper.status_code == 422


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


def test_agent_query_emergency_safety_precedence(mother_client: TestClient):
    """Agent query containing acute emergency symptoms triggers EMERGENCY safety state."""
    response = mother_client.post(
        "/api/v1/agent/query",
        json={"query": "Patient is having severe hemorrhage and convulsion right now."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["safety_state"] == SafetyStatus.EMERGENCY.value
    assert "EMERGENCY CLINICAL NOTICE" in data["response"]

    # Verify safety event was authoritatively saved in DB
    repo = get_repository()
    events = repo.list_safety_events(TEST_MOTHER_ID)
    assert any(e["safety_status"] == SafetyStatus.EMERGENCY.value for e in events)



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
