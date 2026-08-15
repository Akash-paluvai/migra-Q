"""Tests for PostgreSQL fallback policy and health check status."""

import pytest

from backend.core.config import Settings
from backend.db.database import check_database_health


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


def test_development_health_check_reports_degraded_when_postgres_unavailable():
    """Health check returns False (degraded) when PostgreSQL connection fails in dev environment."""
    from backend.core.config import settings

    old_env = settings.APP_ENV
    old_mode = settings.PERSISTENCE_MODE
    try:
        settings.APP_ENV = "development"
        settings.PERSISTENCE_MODE = "postgres"
        # Since PostgreSQL container is not running locally, health check should return False
        assert check_database_health() is False
    finally:
        settings.APP_ENV = old_env
        settings.PERSISTENCE_MODE = old_mode
