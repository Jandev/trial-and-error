"""Tests for the main FastAPI application."""

import pytest
from fastapi.testclient import TestClient

from aspire_backend_service.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root(self, client: TestClient):
        """Test the root endpoint returns hello world."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_startup_health(self, client: TestClient):
        """Test the startup health probe."""
        response = client.get("/health/startup")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_liveness_health(self, client: TestClient):
        """Test the liveness health probe."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_readiness_health(self, client: TestClient):
        """Test the readiness health probe."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
