"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_get_emissions():
    """Test emissions endpoint."""
    response = client.get("/api/v1/emissions/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_emissions_summary():
    """Test emissions summary endpoint."""
    response = client.get("/api/v1/emissions/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_emissions_kg_co2" in data
    assert "building_count" in data


def test_get_hotspots():
    """Test hotspots endpoint."""
    response = client.get("/api/v1/hotspots/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_policy_query():
    """Test policy query endpoint."""
    response = client.post(
        "/api/v1/policy/query",
        json={"question": "What are the emissions targets?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "confidence" in data


def test_generate_forecast():
    """Test forecast endpoint."""
    response = client.post(
        "/api/v1/predictions/forecast",
        json={
            "building_id": "B001",
            "periods": 7,
            "frequency": "D"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

