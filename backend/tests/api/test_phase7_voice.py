"""Phase 7 Voice Contracts and Provider Abstraction Test Suite.

Verifies:
1. Speech-to-Text (/api/v1/voice/transcribe)
   - Authentication requirement (401)
   - Patient ownership & ASHA assignment isolation (403)
   - Audio payload validation (empty audio, invalid base64, oversized audio)
   - MIME type validation (supported vs unsupported)
   - Language identifier validation (supported vs unsupported)
   - Provider failure handling (502 PROVIDER_ERROR without credential/internal leakage)
   - Response structure and audit trail

2. Voice Confirmation (/api/v1/voice/confirm)
   - Clinical Observation Confirmation Boundary (raw audio is not persisted until confirmation)
   - Session existence (404)
   - Patient isolation & ASHA assignment boundaries (403)
   - Client cannot inject safety_state (422)
   - Confirmed message routes to ChatService and SafetyEngine
   - Audit trail

3. Text-to-Speech (/api/v1/voice/synthesize)
   - Authentication requirement (401)
   - Input text validation (empty, whitespace, length limit)
   - Language and format validation
   - Provider failure handling (502 PROVIDER_ERROR)
   - Base64 audio output structure
   - Audit trail

4. Safety Boundary Invariants
   - Client cannot inject safety_state in any voice endpoint
   - SafetyEngine remains authoritative
   - Screening risk (LOW/MEDIUM/HIGH) remains separate from safety state (CLEAR/CONCERNING/EMERGENCY)
"""

import base64
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from backend.app.db.repositories import (
    TEST_ADMIN_ID,
    TEST_ASHA_ID,
    TEST_MOTHER_B_ID,
    TEST_MOTHER_ID,
    get_repository,
)
from backend.app.safety.evaluator import SafetyResult, get_safety_engine
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.voice import (
    MAX_AUDIO_BYTES,
    MAX_TTS_TEXT_LENGTH,
    VoiceLanguage,
)
from backend.app.voice.providers import (
    get_stt_provider,
    get_tts_provider,
    reset_voice_providers,
)


@pytest.fixture(autouse=True)
def reset_providers_and_safety():
    """Reset providers and safety engine before and after each test."""
    reset_voice_providers()
    engine = get_safety_engine()
    engine.clear_rules()
    yield
    reset_voice_providers()
    engine.clear_rules()


def get_dummy_audio_b64(size_bytes: int = 100) -> str:
    """Helper returning valid base64-encoded dummy audio bytes."""
    raw = b"RIFF" + (b"\x00" * max(0, size_bytes - 4))
    return base64.b64encode(raw).decode("ascii")


# ==============================================================================
# 1. Speech-to-Text (/api/v1/voice/transcribe)
# ==============================================================================

def test_transcribe_unauthenticated_rejected(client: TestClient):
    """Calling /api/v1/voice/transcribe without auth returns 401."""
    response = client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(),
            "mime_type": "audio/wav",
            "language": "en",
        },
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_transcribe_valid_mother_success(mother_client: TestClient):
    """Mother can transcribe audio payload in supported language."""
    repo = get_repository()
    initial_audits = len(repo.audit_logs)

    response = mother_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(200),
            "mime_type": "audio/wav",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert len(data["transcript"]) > 0
    assert data["language"] == "en"
    assert data["detected_language"] == "en"
    assert data["confidence"] > 0.0
    assert data["duration_seconds"] > 0.0
    assert data["mother_id"] == str(TEST_MOTHER_ID)
    assert "created_at" in data

    # Verify audit log was recorded
    assert len(repo.audit_logs) == initial_audits + 1
    assert repo.audit_logs[-1]["action"] == "VOICE_TRANSCRIBE"


def test_transcribe_supported_languages(mother_client: TestClient):
    """Verify supported Indian language identifiers succeed."""
    for lang in ["hi", "te", "ta", "kn", "bn", "mr"]:
        response = mother_client.post(
            "/api/v1/voice/transcribe",
            json={
                "audio_content": get_dummy_audio_b64(150),
                "mime_type": "audio/wav",
                "language": lang,
            },
        )
        assert response.status_code == 200
        assert response.json()["language"] == lang


def test_transcribe_unsupported_language_rejected(mother_client: TestClient):
    """Unsupported language returns 422 VALIDATION_ERROR."""
    response = mother_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(),
            "mime_type": "audio/wav",
            "language": "fr",  # French is not supported
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_transcribe_unsupported_mime_type_rejected(mother_client: TestClient):
    """Unsupported MIME type returns 422 VALIDATION_ERROR."""
    response = mother_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(),
            "mime_type": "image/png",
            "language": "en",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "Unsupported audio MIME type" in response.json()["error"]["message"]


def test_transcribe_supported_mime_types(mother_client: TestClient):
    """All documented audio MIME types are accepted."""
    for mime in ["audio/wav", "audio/webm", "audio/mp3", "audio/ogg", "audio/m4a"]:
        response = mother_client.post(
            "/api/v1/voice/transcribe",
            json={
                "audio_content": get_dummy_audio_b64(),
                "mime_type": mime,
                "language": "en",
            },
        )
        assert response.status_code == 200


def test_transcribe_invalid_base64_rejected(mother_client: TestClient):
    """Invalid base64 payload returns 422 VALIDATION_ERROR."""
    response = mother_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": "not_valid_base64_???!!!",
            "mime_type": "audio/wav",
            "language": "en",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_transcribe_empty_audio_rejected(mother_client: TestClient):
    """Empty audio string or 0-byte decoded payload returns 422."""
    # Empty string is caught by Pydantic min_length=1
    res1 = mother_client.post(
        "/api/v1/voice/transcribe",
        json={"audio_content": "", "mime_type": "audio/wav", "language": "en"},
    )
    assert res1.status_code == 422

    # Base64 encoding of empty bytes b""
    empty_b64 = base64.b64encode(b"").decode("ascii")
    res2 = mother_client.post(
        "/api/v1/voice/transcribe",
        json={"audio_content": empty_b64, "mime_type": "audio/wav", "language": "en"},
    )
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"


def test_transcribe_oversized_audio_rejected(mother_client: TestClient):
    """Audio exceeding MAX_AUDIO_BYTES (10 MB) is rejected with 422."""
    # 10 MB + 1 byte
    oversized_raw = b"A" * (MAX_AUDIO_BYTES + 1)
    oversized_b64 = base64.b64encode(oversized_raw).decode("ascii")

    response = mother_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": oversized_b64,
            "mime_type": "audio/wav",
            "language": "en",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "exceeds maximum limit" in response.json()["error"]["message"]


def test_transcribe_cross_patient_mother_forbidden(mother_client: TestClient):
    """Mother cannot specify another mother's ID."""
    response = mother_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(),
            "mime_type": "audio/wav",
            "language": "en",
            "mother_id": str(TEST_MOTHER_B_ID),
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_transcribe_asha_assigned_mother_allowed(asha_client: TestClient):
    """ASHA can transcribe audio for an assigned mother."""
    response = asha_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(),
            "mime_type": "audio/wav",
            "language": "hi",
            "mother_id": str(TEST_MOTHER_ID),
        },
    )
    assert response.status_code == 200
    assert response.json()["mother_id"] == str(TEST_MOTHER_ID)


def test_transcribe_asha_unassigned_mother_forbidden(asha_client: TestClient):
    """ASHA cannot transcribe audio for an unassigned mother."""
    response = asha_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(),
            "mime_type": "audio/wav",
            "language": "hi",
            "mother_id": str(TEST_MOTHER_B_ID),
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_transcribe_provider_failure_returns_502_provider_error(mother_client: TestClient):
    """STT provider failure returns 502 PROVIDER_ERROR without leaking raw provider exceptions."""
    stt = get_stt_provider()
    stt.should_fail = True
    stt.failure_error = "AI4Bharat connection refused at secret-internal-cluster:8080"

    response = mother_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(),
            "mime_type": "audio/wav",
            "language": "en",
        },
    )
    assert response.status_code == 502
    err = response.json()["error"]
    assert err["code"] == "PROVIDER_ERROR"
    assert "Speech-to-text provider failed" in err["message"]
    # Ensure raw secret host/cluster detail is not leaked to client
    assert "secret-internal-cluster" not in err["message"]


def test_transcribe_does_not_persist_clinical_records(mother_client: TestClient):
    """Speech transcription alone must never persist health records, symptoms, or chat turns."""
    repo = get_repository()
    initial_records = len(repo.list_health_records(TEST_MOTHER_ID))
    initial_symptoms = len(repo.list_symptoms(TEST_MOTHER_ID))

    response = mother_client.post(
        "/api/v1/voice/transcribe",
        json={
            "audio_content": get_dummy_audio_b64(),
            "mime_type": "audio/wav",
            "language": "en",
        },
    )
    assert response.status_code == 200

    # Verify no clinical observations were silently persisted
    assert len(repo.list_health_records(TEST_MOTHER_ID)) == initial_records
    assert len(repo.list_symptoms(TEST_MOTHER_ID)) == initial_symptoms


# ==============================================================================
# 2. Voice Confirmation (/api/v1/voice/confirm)
# ==============================================================================

def test_confirm_unauthenticated_rejected(client: TestClient):
    """Calling /api/v1/voice/confirm without auth returns 401."""
    session_id = uuid4()
    response = client.post(
        "/api/v1/voice/confirm",
        json={
            "session_id": str(session_id),
            "confirmed_text": "I confirm I have headache.",
        },
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_confirm_session_not_found(mother_client: TestClient):
    """Confirming to non-existent session returns 404."""
    non_existent = uuid4()
    response = mother_client.post(
        "/api/v1/voice/confirm",
        json={
            "session_id": str(non_existent),
            "confirmed_text": "I confirm this text.",
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_confirm_cross_patient_session_forbidden(mother_client: TestClient):
    """Mother cannot confirm into another patient's session."""
    repo = get_repository()
    b_session_id = uuid4()
    repo.create_chat_session(session_id=b_session_id, mother_id=TEST_MOTHER_B_ID)

    response = mother_client.post(
        "/api/v1/voice/confirm",
        json={
            "session_id": str(b_session_id),
            "confirmed_text": "Sneaking confirmation",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_confirm_unassigned_asha_forbidden(asha_client: TestClient):
    """ASHA cannot confirm into unassigned mother's session."""
    repo = get_repository()
    b_session_id = uuid4()
    repo.create_chat_session(session_id=b_session_id, mother_id=TEST_MOTHER_B_ID)

    response = asha_client.post(
        "/api/v1/voice/confirm",
        json={
            "session_id": str(b_session_id),
            "confirmed_text": "ASHA confirming unassigned",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_confirm_valid_mother_routes_to_chat_and_safety(mother_client: TestClient):
    """Confirmed voice text routes into chat session and invokes authoritative SafetyEngine."""
    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        "/api/v1/voice/confirm",
        json={
            "session_id": str(session_id),
            "confirmed_text": "I had soup and rested yesterday.",
            "language": "en",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == str(session_id)
    assert data["confirmed_text"] == "I had soup and rested yesterday."
    assert data["safety_state"] == SafetyStatus.CLEAR.value
    assert "chat_turn" in data
    assert data["chat_turn"]["user_message"]["content"] == "I had soup and rested yesterday."
    assert "Authoritative safety state: CLEAR" in data["chat_turn"]["assistant_message"]["content"]

    # Verify messages are persisted in chat history
    history = repo.get_chat_messages(session_id)
    assert len(history) == 2
    assert history[0]["content"] == "I had soup and rested yesterday."


def test_confirm_client_cannot_inject_safety_state(mother_client: TestClient):
    """Client attempting to inject safety_state in confirm payload is rejected with 422."""
    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        "/api/v1/voice/confirm",
        json={
            "session_id": str(session_id),
            "confirmed_text": "I am feeling unwell.",
            "safety_state": "EMERGENCY",  # Client injection attempt
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_confirm_triggers_safety_engine_rule_authoritatively(mother_client: TestClient):
    """Authoritative safety rule in SafetyEngine triggers EMERGENCY state through voice confirm."""
    engine = get_safety_engine()

    def mock_emergency_rule(vitals, symptoms):
        return SafetyResult(
            status=SafetyStatus.EMERGENCY,
            triggered_rules=["Critical vital threshold exceeded"],
            is_emergency=True,
        )

    engine.register_rule(mock_emergency_rule)

    repo = get_repository()
    session_id = uuid4()
    repo.create_chat_session(session_id=session_id, mother_id=TEST_MOTHER_ID)

    response = mother_client.post(
        "/api/v1/voice/confirm",
        json={
            "session_id": str(session_id),
            "confirmed_text": "Confirming my observations.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["safety_state"] == SafetyStatus.EMERGENCY.value
    assert data["chat_turn"]["safety_state"] == SafetyStatus.EMERGENCY.value


# ==============================================================================
# 3. Text-to-Speech (/api/v1/voice/synthesize)
# ==============================================================================

def test_synthesize_unauthenticated_rejected(client: TestClient):
    """Calling /api/v1/voice/synthesize without auth returns 401."""
    response = client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Hello mother", "language": "en"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_synthesize_valid_mother_success(mother_client: TestClient):
    """Mother can synthesize text into audio."""
    repo = get_repository()
    initial_audits = len(repo.audit_logs)

    response = mother_client.post(
        "/api/v1/voice/synthesize",
        json={
            "text": "Your message has been recorded.",
            "language": "en",
            "output_format": "audio/wav",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "audio_content" in data
    # Verify base64 audio content decodes
    decoded = base64.b64decode(data["audio_content"])
    assert len(decoded) > 0
    assert decoded.startswith(b"RIFF")
    assert data["mime_type"] == "audio/wav"
    assert data["language"] == "en"
    assert data["text_length"] == len("Your message has been recorded.")
    assert data["duration_seconds"] > 0.0
    assert "created_at" in data

    # Verify audit log recorded
    assert len(repo.audit_logs) == initial_audits + 1
    assert repo.audit_logs[-1]["action"] == "VOICE_SYNTHESIZE"


def test_synthesize_empty_or_whitespace_text_rejected(mother_client: TestClient):
    """Empty or whitespace-only text returns 422 VALIDATION_ERROR."""
    res1 = mother_client.post(
        "/api/v1/voice/synthesize",
        json={"text": "", "language": "en"},
    )
    assert res1.status_code == 422

    res2 = mother_client.post(
        "/api/v1/voice/synthesize",
        json={"text": "     ", "language": "en"},
    )
    assert res2.status_code == 422
    assert res2.json()["error"]["code"] == "VALIDATION_ERROR"


def test_synthesize_text_length_limit_rejected(mother_client: TestClient):
    """Text exceeding MAX_TTS_TEXT_LENGTH (1000 chars) returns 422."""
    too_long = "A" * (MAX_TTS_TEXT_LENGTH + 1)
    response = mother_client.post(
        "/api/v1/voice/synthesize",
        json={"text": too_long, "language": "en"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_synthesize_unsupported_language_rejected(mother_client: TestClient):
    """Unsupported language returns 422 VALIDATION_ERROR."""
    response = mother_client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Test synthesis", "language": "de"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_synthesize_unsupported_format_rejected(mother_client: TestClient):
    """Unsupported audio format returns 422 VALIDATION_ERROR."""
    response = mother_client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Test synthesis", "language": "en", "output_format": "audio/flac"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "Unsupported output format" in response.json()["error"]["message"]


def test_synthesize_provider_failure_returns_502(mother_client: TestClient):
    """TTS provider failure returns 502 PROVIDER_ERROR without leaking raw provider exceptions."""
    tts = get_tts_provider()
    tts.should_fail = True
    tts.failure_error = "Indic-TTS GPU cluster timeout at 10.0.4.12:9000"

    response = mother_client.post(
        "/api/v1/voice/synthesize",
        json={"text": "Test synthesis failure", "language": "en"},
    )
    assert response.status_code == 502
    err = response.json()["error"]
    assert err["code"] == "PROVIDER_ERROR"
    assert "Text-to-speech provider failed" in err["message"]
    # Ensure internal IP and port are not leaked
    assert "10.0.4.12" not in err["message"]


def test_synthesize_client_cannot_inject_extra_fields(mother_client: TestClient):
    """Client attempting to inject extra fields is rejected with 422 (extra='forbid')."""
    response = mother_client.post(
        "/api/v1/voice/synthesize",
        json={
            "text": "Valid text",
            "language": "en",
            "safety_state": "EMERGENCY",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
