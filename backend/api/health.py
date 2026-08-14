"""Health check endpoints with real dependency verification."""

from fastapi import APIRouter

from backend.db.database import check_database_health

router = APIRouter()


@router.get("/health")
def root_health() -> dict:
    """Minimal liveness probe."""
    return {"status": "ok"}


@router.get("/api/v1/health")
def detailed_health() -> dict:
    """Readiness probe with actual PostgreSQL connectivity check."""
    db_ok = check_database_health()
    status = "ok" if db_ok else "degraded"
    return {
        "status": status,
        "service": "migra-q",
        "database": "ok" if db_ok else "unavailable",
    }
