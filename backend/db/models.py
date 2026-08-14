"""SQLAlchemy database models for execution audit logging."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from backend.db.database import Base


class ExecutionRecord(Base):
    """PostgreSQL table storing execution audit records."""

    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(64), unique=True, index=True, nullable=False)
    query_hash = Column(String(64), index=True, nullable=False)
    dataset_id = Column(String(128), index=True, nullable=False)
    dataset_hash = Column(String(64), nullable=False)
    execution_mode = Column(String(32), nullable=False, default="SOURCE")
    status = Column(String(32), nullable=False)
    engine = Column(String(32), nullable=False, default="duckdb")
    engine_version = Column(String(32), nullable=False, default="1.0")
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    duration_ms = Column(Float, nullable=False, default=0.0)
    row_count = Column(Integer, nullable=False, default=0)
    result_artifact = Column(String(512), nullable=True)
    error_code = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
