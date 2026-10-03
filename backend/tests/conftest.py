"""Pytest configuration and shared fixtures for backend tests."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import Settings, get_settings


@pytest.fixture
def client() -> TestClient:
    """Provide a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_settings() -> Settings:
    """Provide default application settings for testing."""
    return get_settings()
