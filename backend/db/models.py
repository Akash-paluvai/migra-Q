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


class AIDiagnosisRecord(Base):
    """PostgreSQL table storing AI diagnosis run audit records."""

    __tablename__ = "ai_diagnoses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnosis_id = Column(String(64), unique=True, index=True, nullable=False)
    discrepancy_id = Column(String(64), index=True, nullable=False)
    provider = Column(String(32), nullable=False)
    model = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    observed_change = Column(Text, nullable=True)
    likely_mechanism = Column(Text, nullable=True)
    possible_cause = Column(Text, nullable=True)
    uncertainty = Column(Text, nullable=True)
    diagnosis_confidence = Column(Float, nullable=False, default=0.0)
    claims_json = Column(Text, nullable=True)
    context_hash = Column(String(64), index=True, nullable=False)
    prompt_hash = Column(String(64), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    duration_ms = Column(Float, nullable=False, default=0.0)
    token_usage_json = Column(Text, nullable=True)
    error_code = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)
    diagnosis_ai_version = Column(String(32), nullable=False, default="0.1.0")
    prompt_version = Column(String(32), nullable=False, default="0.1.0")


class RepairProposalRecord(Base):
    """PostgreSQL table storing candidate repair proposal audit records."""

    __tablename__ = "repair_proposals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(String(64), unique=True, index=True, nullable=False)
    diagnosis_id = Column(String(64), index=True, nullable=False)
    discrepancy_id = Column(String(64), index=True, nullable=False)
    status = Column(String(32), nullable=False)
    original_sql = Column(Text, nullable=True)
    proposed_sql = Column(Text, nullable=True)
    changed_region = Column(String(256), nullable=True)
    rationale = Column(Text, nullable=True)
    expected_effect = Column(Text, nullable=True)
    repair_confidence = Column(Float, nullable=False, default=0.0)
    claims_json = Column(Text, nullable=True)
    constraints_checked_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RepairChangeRecordModel(Base):
    """PostgreSQL table storing individual patch changes for a repair proposal."""

    __tablename__ = "repair_changes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repair_id = Column(String(64), index=True, nullable=False)
    location = Column(String(256), nullable=False)
    before_expression = Column(Text, nullable=False)
    after_expression = Column(Text, nullable=False)
    change_type = Column(String(32), nullable=False, default="MODIFY")


class RepairVerificationRecordModel(Base):
    """PostgreSQL table storing Phase 8 repair verification audit results."""

    __tablename__ = "repair_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    verification_id = Column(String(64), unique=True, index=True, nullable=False)
    repair_id = Column(String(64), index=True, nullable=False)
    discrepancy_id = Column(String(64), index=True, nullable=False)
    validation_id_before = Column(String(64), nullable=False)
    validation_id_after = Column(String(64), nullable=True)
    execution_id_before = Column(String(64), nullable=False)
    execution_id_repaired = Column(String(64), nullable=True)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    verification_version = Column(String(32), nullable=False, default="1.0.0")
    original_discrepancy_count = Column(Integer, nullable=False, default=0)
    remaining_discrepancy_count = Column(Integer, nullable=False, default=0)
    new_discrepancy_count = Column(Integer, nullable=False, default=0)
    resolved_discrepancy_count = Column(Integer, nullable=False, default=0)
    affected_rows_before = Column(Integer, nullable=False, default=0)
    affected_rows_after = Column(Integer, nullable=False, default=0)
    affected_percentage_before = Column(Float, nullable=False, default=0.0)
    affected_percentage_after = Column(Float, nullable=False, default=0.0)
    reduction_count = Column(Integer, nullable=False, default=0)
    reduction_percentage = Column(Float, nullable=False, default=0.0)
    summary_json = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)
    rejection_reason = Column(String(128), nullable=True)
    error_code = Column(String(128), nullable=True)
    error_message = Column(Text, nullable=True)


class RepairOutcomeRecordModel(Base):
    """PostgreSQL table storing individual discrepancy repair outcomes."""

    __tablename__ = "repair_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    verification_id = Column(String(64), index=True, nullable=False)
    discrepancy_id_before = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    affected_rows_before = Column(Integer, nullable=False, default=0)
    affected_rows_after = Column(Integer, nullable=False, default=0)
    reduction_count = Column(Integer, nullable=False, default=0)
    reduction_percentage = Column(Float, nullable=False, default=0.0)
    matching_after_discrepancy_ids_json = Column(Text, nullable=True)
    new_discrepancy_ids_json = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)


class MigrationRecordModel(Base):
    """PostgreSQL table storing Phase 9 migration records."""

    __tablename__ = "migrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    migration_id = Column(String(64), unique=True, index=True, nullable=False)
    source_dialect = Column(String(32), nullable=False)
    target_dialect = Column(String(32), nullable=False)
    source_sql_hash = Column(String(64), nullable=False)
    normalized_sql_hash = Column(String(64), nullable=True)
    source_sql = Column(Text, nullable=True)
    source_sql_storage = Column(String(32), nullable=False, default="database")
    source_sql_ref = Column(String(256), nullable=True)
    dataset_id = Column(String(128), nullable=False)
    dataset_hash = Column(String(64), nullable=False)
    current_state = Column(String(32), nullable=False, default="CREATED")
    final_status = Column(String(32), nullable=False, default="IN_PROGRESS")
    assurance_score = Column(Float, nullable=True)
    evidence_coverage = Column(Float, nullable=True)
    assurance_version = Column(String(32), nullable=False, default="1.0.0")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MigrationStateEventModel(Base):
    """PostgreSQL table storing Phase 9 state transition events."""

    __tablename__ = "migration_state_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    migration_id = Column(String(64), index=True, nullable=False)
    from_state = Column(String(32), nullable=False)
    to_state = Column(String(32), nullable=False)
    reason = Column(Text, nullable=True)
    artifact_id = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class MigrationAssuranceReportModel(Base):
    """PostgreSQL table storing Phase 9 assurance reports."""

    __tablename__ = "migration_assurance_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    migration_id = Column(String(64), unique=True, index=True, nullable=False)
    assurance_version = Column(String(32), nullable=False, default="1.0.0")
    final_status = Column(String(32), nullable=False)
    decision_reason = Column(Text, nullable=True)
    verification_path = Column(String(32), nullable=False)
    evidence_score = Column(Float, nullable=True)
    evidence_coverage = Column(Float, nullable=True)
    band = Column(String(32), nullable=True)
    report_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

