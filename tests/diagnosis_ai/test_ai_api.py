"""Integration tests for Phase 7 FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.db.database import init_db
from backend.main import app


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


client = TestClient(app)


def test_api_create_ai_diagnosis_endpoint():
    source_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

    target_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

    payload = {
        "discrepancy_id": "D-001",
        "category": "BOUNDARY_CONDITION",
        "severity": "HIGH",
        "source_sql": source_sql,
        "target_sql": target_sql,
        "source_dialect": "teradata",
        "target_dialect": "bigquery",
        "source_expression": "t.amount > 500",
        "target_expression": "t.amount >= 500",
        "affected_row_count": 10512,
        "affected_percentage": 10.51,
        "representative_examples": [{"customer_id": "C18291", "refund": 500.0}],
        "mock_mode": "MOCK_BOUNDARY_REPAIR",
    }
    resp = client.post("/api/v1/ai-diagnoses", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert "diagnosis" in data
    assert "repair_proposal" in data
    assert data["diagnosis"]["status"] == "DIAGNOSED"
    assert data["repair_proposal"]["status"] == "PROPOSED"
    assert data["repair_proposal"]["proposed_sql"] != ""

    diag_id = data["metadata"]["diagnosis_id"]
    rep_id = data["repair_proposal"]["repair_id"]

    from backend.db.database import check_database_health

    if check_database_health():
        # GET diagnosis
        get_diag = client.get(f"/api/v1/ai-diagnoses/{diag_id}")
        assert get_diag.status_code == 200
        assert get_diag.json()["metadata"]["diagnosis_id"] == diag_id

        # GET repair proposal
        get_rep = client.get(f"/api/v1/repair-proposals/{rep_id}")
        assert get_rep.status_code == 200
        assert get_rep.json()["repair_id"] == rep_id
