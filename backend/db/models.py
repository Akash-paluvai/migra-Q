"""SQLAlchemy database models for execution and validation audit logging."""

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


class ValidationRecord(Base):
    """PostgreSQL table storing validation run audit records."""

    __tablename__ = "validations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    validation_id = Column(String(64), unique=True, index=True, nullable=False)
    source_execution_id = Column(String(64), index=True, nullable=False)
    target_execution_id = Column(String(64), index=True, nullable=False)
    dataset_id = Column(String(128), index=True, nullable=False)
    status = Column(String(32), nullable=False)
    validator_version = Column(String(32), nullable=False, default="0.1.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    summary_json = Column(Text, nullable=True)


class ValidationResultRecord(Base):
    """PostgreSQL table storing individual validation check results."""

    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    validation_id = Column(String(64), index=True, nullable=False)
    check_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    severity = Column(String(32), nullable=False)
    score = Column(Float, nullable=False, default=0.0)
    mismatch_count = Column(Integer, nullable=False, default=0)
    summary = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    duration_ms = Column(Float, nullable=False, default=0.0)


class DiagnosisRecord(Base):
    """PostgreSQL table storing diagnosis run audit records."""

    __tablename__ = "diagnoses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnosis_id = Column(String(64), unique=True, index=True, nullable=False)
    validation_id = Column(String(64), index=True, nullable=False)
    classifier_version = Column(String(32), nullable=False, default="0.1.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    summary_json = Column(Text, nullable=True)


class DiscrepancyRecordModel(Base):
    """PostgreSQL table storing individual discrepancy records."""

    __tablename__ = "discrepancies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnosis_id = Column(String(64), index=True, nullable=False)
    discrepancy_id = Column(String(32), nullable=False)  # D-001 ...
    category = Column(String(64), nullable=False)
    subcategory = Column(String(64), nullable=True)
    severity = Column(String(32), nullable=False)
    classification_confidence = Column(Float, nullable=False, default=1.0)
    source_location = Column(String(256), nullable=True)
    target_location = Column(String(256), nullable=True)
    source_expression = Column(Text, nullable=True)
    target_expression = Column(Text, nullable=True)
    affected_row_count = Column(Integer, nullable=False, default=0)
    affected_percentage = Column(Float, nullable=False, default=0.0)
    status = Column(String(32), nullable=False, default="OPEN")
    reason = Column(Text, nullable=True)
    analysis_path = Column(String(256), nullable=True)
    discrepancy_signature = Column(String(64), nullable=False)
    metadata_json = Column(Text, nullable=True)


class DiscrepancyEvidenceRecordModel(Base):
    """PostgreSQL table storing evidence items for a discrepancy."""

    __tablename__ = "discrepancy_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discrepancy_id = Column(String(64), index=True, nullable=False)
    evidence_type = Column(String(64), nullable=False)
    evidence_json = Column(Text, nullable=False)
    ordinal = Column(Integer, nullable=False, default=1)


class TranslationRecord(Base):
    """PostgreSQL table storing translation audit records."""

    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    translation_id = Column(String(64), unique=True, index=True, nullable=False)
    request_id = Column(String(64), index=True, nullable=False)
    source_dialect = Column(String(32), nullable=False)
    target_dialect = Column(String(32), nullable=False)
    source_sql_hash = Column(String(64), index=True, nullable=False)
    translation_context_hash = Column(String(64), index=True, nullable=False)
    prompt_hash = Column(String(64), index=True, nullable=False)
    provider = Column(String(32), nullable=False)
    model = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    candidate_validation_status = Column(String(32), nullable=True)
    target_sql = Column(Text, nullable=True)
    assumptions_json = Column(Text, nullable=True)
    potential_risks_json = Column(Text, nullable=True)
    translated_rules_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    duration_ms = Column(Float, nullable=False, default=0.0)
    retry_count = Column(Integer, nullable=False, default=0)
    token_usage_json = Column(Text, nullable=True)
    error_code = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    translator_version = Column(String(32), nullable=False, default="0.1.0")
    prompt_version = Column(String(32), nullable=False, default="0.1.0")

