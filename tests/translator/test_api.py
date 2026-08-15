"""Unit tests for Translation Engine API endpoints."""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_api_create_translation_success():
    payload = {
        "source_sql": (
            "SELECT customer_id, SUM(amount) FROM transactions "
            "WHERE amount > 500 GROUP BY customer_id;"
        ),
        "source_dialect": "teradata",
        "target_dialect": "bigquery",
    }
    response = client.post("/api/v1/translations?mock_mode=MOCK_GOOD", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["candidate_validation_status"] == "VALID_SYNTAX"
    assert data["validation_summary"] == "Candidate SQL syntactically valid"
    assert "metadata" in data
    assert "response" in data
    assert data["response"]["target_sql"] != ""


def test_api_create_translation_unsafe_sql():
    payload = {
        "source_sql": "SELECT * FROM customers;",
        "source_dialect": "teradata",
        "target_dialect": "bigquery",
    }
    response = client.post("/api/v1/translations?mock_mode=MOCK_UNSAFE_SQL", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "REJECTED"
    assert data["candidate_validation_status"] == "UNSAFE_SQL"


def test_api_get_translation_not_found():
    response = client.get("/api/v1/translations/trans-nonexistent")
    assert response.status_code == 404
