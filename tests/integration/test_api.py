from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_migration():
    payload = {
        "source_dialect": "oracle",
        "target_dialect": "postgres",
        "source_sql": "SELECT id, NVL(amount, 0) FROM transactions"
    }
    response = client.post("/api/v1/migrations/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "migration_id" in data
    assert data["status"] == "translated"
