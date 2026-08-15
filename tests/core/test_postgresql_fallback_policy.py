"""Tests for PostgreSQL fallback policy and health check status."""

import pytest

from backend.core.config import Settings


def test_test_mode_can_use_memory_persistence():
    """Test environment allows PERSISTENCE_MODE='memory'."""
    s = Settings(APP_ENV="test", PERSISTENCE_MODE="memory")
    s.validate_persistence_policy()
    assert s.PERSISTENCE_MODE == "memory"


def test_non_test_mode_rejects_memory_persistence():
    """Non-test environment raises ValueError if PERSISTENCE_MODE is not 'postgres'."""
    s = Settings(APP_ENV="development", PERSISTENCE_MODE="memory")
    with pytest.raises(ValueError, match="PostgreSQL is mandatory"):
        s.validate_persistence_policy()


def test_development_health_check_reports_degraded_when_postgres_unavailable(monkeypatch):
    """Health check returns False (degraded) when PostgreSQL connection fails in dev environment."""
    from backend.db import database

    def mock_failed_connect():
        raise RuntimeError("Database connection unreachable")

    monkeypatch.setattr(database.engine, "connect", mock_failed_connect)
    assert database.check_database_health() is False
