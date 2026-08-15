"""Unit tests for RepairExecutor execution adapter."""

import pytest

from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.repair_verification.exceptions import ExecutionFailedError
from backend.repair_verification.executor import RepairExecutor


def test_repair_executor_success(monkeypatch):
    mock_res = ExecutionResult(
        execution_id="exec-rep-1",
        query_hash="hash123",
        dataset_id="customer_risk",
        dataset_hash="dshash123",
        execution_mode="TARGET",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T12:00:00Z",
        duration_ms=10.5,
        row_count=100,
    )
    monkeypatch.setattr(
        "backend.execution.service.ExecutionService.execute",
        lambda req: mock_res,
    )

    res = RepairExecutor.execute_repaired_sql(
        proposed_sql="SELECT * FROM t WHERE val > 500;",
        dataset_id="customer_risk",
        target_dialect="bigquery",
    )
    assert res.execution_id == "exec-rep-1"
    assert res.status == ExecutionStatus.SUCCESS


def test_repair_executor_handles_failure(monkeypatch):
    failed_res = ExecutionResult(
        execution_id="exec-failed",
        query_hash="hash123",
        dataset_id="customer_risk",
        dataset_hash="dshash123",
        execution_mode="TARGET",
        status=ExecutionStatus.EXECUTION_ERROR,
        timestamp="2026-08-15T12:00:00Z",
        duration_ms=5.0,
        error_code="TABLE_NOT_FOUND",
        error_message="Table 'missing_table' not found",
    )
    monkeypatch.setattr(
        "backend.execution.service.ExecutionService.execute",
        lambda req: failed_res,
    )

    with pytest.raises(ExecutionFailedError) as exc_info:
        RepairExecutor.execute_repaired_sql(
            proposed_sql="SELECT * FROM missing_table;",
            dataset_id="customer_risk",
            target_dialect="bigquery",
        )
    assert exc_info.value.error_code == "TABLE_NOT_FOUND"
