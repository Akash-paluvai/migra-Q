"""Phase 0 tests: health endpoints, database check, DuckDB availability."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_root_health():
    """GET /health returns {"status": "ok"}."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_detailed_health_db_available():
    """GET /api/v1/health with healthy database."""
    with patch("backend.api.health.check_database_health", return_value=True):
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "migra-q"
    assert data["database"] == "ok"


def test_detailed_health_db_unavailable():
    """GET /api/v1/health when database is down returns degraded status."""
    with patch("backend.api.health.check_database_health", return_value=False):
        resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["database"] == "unavailable"


def test_duckdb_available():
    """DuckDB must be importable and execute SELECT 1."""
    from backend.db.duckdb_check import check_duckdb

    assert check_duckdb() is True
