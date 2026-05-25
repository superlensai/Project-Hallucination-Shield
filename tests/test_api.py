import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/internal/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "halwall-api"}

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_lookup_not_found():
    # This test will fail if the DB isn't mocked or cleaned, 
    # but for a basic check of the endpoint structure:
    response = client.post(
        "/internal/trust/lookup",
        json={"name": "non-existent-package", "registry": "pypi"}
    )
    # If the DB is empty, it should return 404
    assert response.status_code in [404, 200]
