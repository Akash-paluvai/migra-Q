"""Health check endpoints with real dependency verification."""

from fastapi import APIRouter

from backend.core.config import settings
from backend.db.database import check_database_health

router = APIRouter()


@router.get("/health")
def root_health() -> dict:
    """Minimal liveness probe."""
    return {"status": "ok"}


@router.get("/api/v1/health")
def detailed_health() -> dict:
    """Readiness probe with actual PostgreSQL connectivity check."""
    settings.validate_persistence_policy()
    db_ok = check_database_health()
    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "service": "migra-q",
        "app_env": settings.APP_ENV,
        "persistence_mode": settings.PERSISTENCE_MODE,
        "database": "ok" if db_ok else "unavailable",
    }
