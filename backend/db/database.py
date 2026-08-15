"""PostgreSQL connection management via SQLAlchemy 2.x."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def get_db() -> Session:  # type: ignore[misc]
    """Yield a database session, closing it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Return a new database session instance."""
    return SessionLocal()


def check_database_health() -> bool:
    """Run a lightweight query to verify PostgreSQL is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.debug("PostgreSQL health check failed: %s", exc)
        return False


def init_db() -> None:
    """Initialize database tables if connected."""
    try:
        import backend.db.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        logger.warning("Could not initialize database tables: %s", exc)
