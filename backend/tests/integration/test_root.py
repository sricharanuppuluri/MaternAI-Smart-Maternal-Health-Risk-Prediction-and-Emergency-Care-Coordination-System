"""Integration tests for application root and openapi documentation."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verify GET / returns 200 and application metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "MaternAI"
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"


def test_openapi_schema_available(client: TestClient):
    """Verify OpenAPI schema is generated and accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "MaternAI API"
    assert "/api/v1/health" in schema["paths"]
    assert "/" in schema["paths"]
