"""Tests for Phase 9 domain models."""


from backend.assurance.models import (
    AssuranceBand,
    ComponentStatus,
    GateOutcome,
    MigrationAssuranceReport,
    MigrationFinalStatus,
    MigrationRecord,
    MigrationState,
    VerificationPath,
)


class TestMigrationStateEnum:
    def test_all_13_states_defined(self):
        assert len(MigrationState) == 13

    def test_terminal_states(self):
        terminals = {MigrationState.VERIFIED, MigrationState.FAILED, MigrationState.BLOCKED, MigrationState.ERROR}
        assert len(terminals) == 4

    def test_state_string_values(self):
        assert MigrationState.CREATED.value == "CREATED"
        assert MigrationState.REPAIR_VERIFYING.value == "REPAIR_VERIFYING"


class TestMigrationFinalStatusEnum:
    def test_all_5_statuses(self):
        assert len(MigrationFinalStatus) == 5

    def test_no_safe_or_production_ready(self):
        values = {s.value for s in MigrationFinalStatus}
        assert "SAFE" not in values
        assert "PRODUCTION_READY" not in values


class TestGateOutcomeEnum:
    def test_pass_fail_not_applicable(self):
        assert GateOutcome.PASS.value == "PASS"
        assert GateOutcome.FAIL.value == "FAIL"
        assert GateOutcome.NOT_APPLICABLE.value == "NOT_APPLICABLE"


class TestComponentStatusEnum:
    def test_scored_not_applicable_error(self):
        assert ComponentStatus.SCORED.value == "SCORED"
        assert ComponentStatus.NOT_APPLICABLE.value == "NOT_APPLICABLE"
        assert ComponentStatus.ERROR.value == "ERROR"


class TestAssuranceBandEnum:
    def test_all_4_bands(self):
        assert len(AssuranceBand) == 4


class TestMigrationRecord:
    def test_default_state(self):
        record = MigrationRecord(
            migration_id="MIG-TEST",
            source_dialect="teradata",
            target_dialect="bigquery",
            source_sql_hash="abc123",
            dataset_id="dev",
            dataset_hash="def456",
        )
        assert record.current_state == MigrationState.CREATED
        assert record.final_status == MigrationFinalStatus.IN_PROGRESS
        assert record.assurance_score is None
        assert record.evidence_coverage is None

    def test_serialization_roundtrip(self):
        record = MigrationRecord(
            migration_id="MIG-TEST",
            source_dialect="teradata",
            target_dialect="bigquery",
            source_sql_hash="abc",
            dataset_id="dev",
            dataset_hash="def",
        )
        json_str = record.model_dump_json()
        restored = MigrationRecord.model_validate_json(json_str)
        assert restored.migration_id == record.migration_id
        assert restored.current_state == record.current_state


class TestMigrationAssuranceReport:
    def test_default_report(self):
        report = MigrationAssuranceReport(migration_id="MIG-001")
        assert report.final_status == MigrationFinalStatus.IN_PROGRESS
        assert report.verification_path == VerificationPath.DIRECT_PASS
        assert report.score.evidence_score == 0.0
        assert report.score.evidence_coverage == 0.0

    def test_report_serialization(self):
        report = MigrationAssuranceReport(
            migration_id="MIG-001",
            final_status=MigrationFinalStatus.VERIFIED,
        )
        json_str = report.model_dump_json()
        restored = MigrationAssuranceReport.model_validate_json(json_str)
        assert restored.final_status == MigrationFinalStatus.VERIFIED
        assert restored.migration_id == "MIG-001"
