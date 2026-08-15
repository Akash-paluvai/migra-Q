"""Unit tests for validation domain models, context, and evidence sampling helpers."""

from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.validation.context import ValidationContext
from backend.validation.helpers import truncate_evidence
from backend.validation.models import (
    EvidenceItem,
    EvidenceType,
    ValidationCheckStatus,
    ValidationReport,
    ValidationResult,
    ValidationSeverity,
)


def mock_execution(exec_id="exec-1"):
    return ExecutionResult(
        execution_id=exec_id,
        query_hash="hash1",
        dataset_id="test",
        dataset_hash="dhash1",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T00:00:00Z",
        row_count=10,
        columns=[],
    )


def test_validation_context_read_only():
    src = mock_execution("src-1")
    tgt = mock_execution("tgt-1")
    ctx = ValidationContext(source_execution=src, target_execution=tgt)

    assert ctx.source_execution.execution_id == "src-1"
    assert ctx.target_execution.execution_id == "tgt-1"
    assert ctx.config.numeric_absolute_tolerance == 1e-6


def test_evidence_item_schema():
    ev = EvidenceItem(
        type=EvidenceType.VALUE_MISMATCH,
        key={"customer_id": "C101"},
        column="status",
        source_value="ACTIVE",
        target_value="INACTIVE",
    )
    assert ev.type == EvidenceType.VALUE_MISMATCH
    assert ev.key["customer_id"] == "C101"


def test_validation_result_contract():
    res = ValidationResult(
        check_name="SchemaValidator",
        status=ValidationCheckStatus.PASS,
        severity=ValidationSeverity.INFO,
        score=1.0,
        summary="Clean match",
    )
    assert res.score == 1.0
    assert res.status == ValidationCheckStatus.PASS


def test_evidence_truncation_helper():
    items = [EvidenceItem(type=EvidenceType.VALUE_MISMATCH, detail=f"item-{i}") for i in range(150)]
    truncated, is_trunc = truncate_evidence(items, max_items=100)

    assert len(truncated) == 100
    assert is_trunc is True


def test_validation_report_summary_aggregation():
    report = ValidationReport(
        validation_id="val-1",
        source_execution_id="src-1",
        target_execution_id="tgt-1",
        dataset_id="dev",
        created_at="2026-08-15T00:00:00Z",
        overall_status="PASS",
        summary={"checks_run": 5, "checks_passed": 5, "checks_failed": 0},
    )
    assert report.overall_status == "PASS"
    assert report.summary["checks_run"] == 5
