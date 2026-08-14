"""DuckDB availability check — embedded dependency, not a Docker service."""

import duckdb

from backend.core.logging import get_logger

logger = get_logger(__name__)


def check_duckdb() -> bool:
    """Verify DuckDB is importable and functional with a trivial query."""
    try:
        result = duckdb.sql("SELECT 1 AS ok").fetchone()
        ok = result is not None and result[0] == 1
        if ok:
            logger.info("DuckDB check passed (version %s)", duckdb.__version__)
        return ok
    except Exception as exc:
        logger.error("DuckDB check failed: %s", exc)
        return False
