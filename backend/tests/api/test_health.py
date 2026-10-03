"""Tests for the API v1 health endpoint."""

from fastapi.testclient import TestClient


def test_api_v1_health_endpoint(client: TestClient):
    """Verify /api/v1/health returns 200 OK and valid health payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "MaternAI"
    assert "version" in data
    assert "environment" in data
