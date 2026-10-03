"""Pytest configuration, shared fixtures, and isolated test authentication overrides."""

from typing import Generator
from uuid import UUID
import pytest
from fastapi.testclient import TestClient

from backend.app.auth.dependencies import get_current_user
from backend.app.core.config import Settings, get_settings
from backend.app.main import app
from backend.app.schemas.auth import AuthUser, UserRole

# Deterministic Test Users for isolated testing
TEST_MOTHER_USER = AuthUser(
    id=UUID("00000000-0000-0000-0000-000000000001"),
    email="mother@example.com",
    role=UserRole.MOTHER,
    full_name="Test Mother",
)

TEST_MOTHER_B_USER = AuthUser(
    id=UUID("00000000-0000-0000-0000-000000000004"),
    email="mother_b@example.com",
    role=UserRole.MOTHER,
    full_name="Mother B",
)

TEST_ASHA_USER = AuthUser(
    id=UUID("00000000-0000-0000-0000-000000000002"),
    email="asha@example.com",
    role=UserRole.ASHA,
    full_name="Test ASHA",
)

TEST_ADMIN_USER = AuthUser(
    id=UUID("00000000-0000-0000-0000-000000000003"),
    email="admin@example.com",
    role=UserRole.ADMIN,
    full_name="System Admin",
)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a clean test client with production authentication dependencies active."""
    app.dependency_overrides.clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def mother_client() -> Generator[TestClient, None, None]:
    """Provide a test client authenticated as a Mother via dependency override."""
    app.dependency_overrides[get_current_user] = lambda: TEST_MOTHER_USER
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def asha_client() -> Generator[TestClient, None, None]:
    """Provide a test client authenticated as an ASHA worker via dependency override."""
    app.dependency_overrides[get_current_user] = lambda: TEST_ASHA_USER
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client() -> Generator[TestClient, None, None]:
    """Provide a test client authenticated as an Admin via dependency override."""
    app.dependency_overrides[get_current_user] = lambda: TEST_ADMIN_USER
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_settings() -> Settings:
    """Provide default application settings for testing."""
    return get_settings()
