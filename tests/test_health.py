"""Tests for the health endpoint."""

from fastapi.testclient import TestClient
from src.reqgate.app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    """Test that /health returns status ok."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_is_json():
    """Test that /health returns JSON content type."""
    response = client.get("/health")

    assert response.headers["content-type"] == "application/json"
