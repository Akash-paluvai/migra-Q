"""Unit tests for ValidationOrchestrator."""

from backend.execution.models import ColumnSchema, ExecutionResult, ExecutionStatus
from backend.validation.context import ValidationContext
from backend.validation.models import ValidationCheckStatus, ValidationConfig, ValidationResult
from backend.validation.orchestrator import ValidationOrchestrator
from backend.validation.validators.base import BaseValidator


def make_exec_sample(cols, sample):
    return ExecutionResult(
        execution_id="exec-1",
        query_hash="h1",
        dataset_id="d1",
        dataset_hash="dh1",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T00:00:00Z",
        row_count=len(sample),
        columns=[ColumnSchema(name=n, type=t) for n, t in cols],
        sample_data=sample,
    )


class PassingValidator(BaseValidator):
    name = "PassingValidator"

    def validate(self, context: ValidationContext) -> ValidationResult:
        return ValidationResult(
            check_name=self.name,
            status=ValidationCheckStatus.PASS,
            score=1.0,
            summary="Pass",
        )


class FailingValidator(BaseValidator):
    name = "FailingValidator"

    def validate(self, context: ValidationContext) -> ValidationResult:
        return ValidationResult(
            check_name=self.name,
            status=ValidationCheckStatus.FAIL,
            score=0.0,
            summary="Fail",
            mismatch_count=1,
        )


class CrashingValidator(BaseValidator):
    name = "CrashingValidator"

    def validate(self, context: ValidationContext) -> ValidationResult:
        raise ValueError("Unexpected explosion!")


def test_orchestrator_all_pass():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    orch = ValidationOrchestrator([PassingValidator()])
    report = orch.validate(ctx)

    assert report.overall_status == "PASS"
    assert report.summary["checks_passed"] == 1
    assert report.summary["checks_failed"] == 0


def test_orchestrator_one_fail_causes_overall_fail():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    orch = ValidationOrchestrator([PassingValidator(), FailingValidator()])
    report = orch.validate(ctx)

    assert report.overall_status == "FAIL"
    assert report.summary["checks_passed"] == 1
    assert report.summary["checks_failed"] == 1


def test_orchestrator_distinguishes_crash_from_failure():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    orch = ValidationOrchestrator([PassingValidator(), CrashingValidator()])
    report = orch.validate(ctx)

    assert report.overall_status == "ERROR"
    assert report.summary["checks_errored"] == 1
    assert report.checks[1].status == ValidationCheckStatus.ERROR
    assert "Unexpected explosion" in report.checks[1].summary


def test_orchestrator_enabled_validators_filter():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        config=ValidationConfig(enabled_validators=["PassingValidator"]),
    )

    orch = ValidationOrchestrator([PassingValidator(), FailingValidator()])
    report = orch.validate(ctx)

    assert report.overall_status == "PASS"
    assert len(report.checks) == 1


def test_orchestrator_continues_on_failure():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    orch = ValidationOrchestrator([FailingValidator(), PassingValidator()])
    report = orch.validate(ctx)

    assert len(report.checks) == 2
    assert report.summary["checks_run"] == 2


def test_orchestrator_generates_uuid_validation_id():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    report = ValidationOrchestrator([PassingValidator()]).validate(ctx)
    assert len(report.validation_id) > 10


def test_orchestrator_captures_created_at():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    report = ValidationOrchestrator([PassingValidator()]).validate(ctx)
    assert "2026" in report.created_at or "T" in report.created_at


def test_orchestrator_default_instantiates_5_validators():
    orch = ValidationOrchestrator()
    assert len(orch.validators) == 5


def test_orchestrator_summary_counts():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    report = ValidationOrchestrator([PassingValidator()]).validate(ctx)
    assert report.summary["checks_run"] == 1
    assert report.summary["checks_passed"] == 1


def test_orchestrator_overall_status_not_production_ready():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    report = ValidationOrchestrator([PassingValidator()]).validate(ctx)
    assert report.overall_status in ("PASS", "WARN", "FAIL", "ERROR")
