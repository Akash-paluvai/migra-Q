"""Unit tests for EdgeCaseValidator."""

from backend.execution.models import ColumnSchema, ExecutionResult, ExecutionStatus
from backend.validation.context import ValidationContext
from backend.validation.models import ValidationCheckStatus
from backend.validation.validators.edge_cases import EdgeCaseValidator


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


def test_edge_case_clean_boundary():
    cols = [("customer_id", "VARCHAR"), ("amount", "DOUBLE")]
    sample = [{"customer_id": "C1", "amount": 499.99}, {"customer_id": "C2", "amount": 500.00}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        benchmark_scenario={"scenario_name": "BOUNDARY_REFUND_001"},
    )

    res = EdgeCaseValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_edge_case_null_count_mismatch():
    cols = [("customer_id", "VARCHAR"), ("closed_at", "VARCHAR")]
    src_sample = [{"customer_id": "C1", "closed_at": None}]
    tgt_sample = [{"customer_id": "C1", "closed_at": "9999-12-31"}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        benchmark_scenario={"scenario_name": "NULL_001"},
    )

    res = EdgeCaseValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.evidence[0].category == "NULL_SEMANTICS"


def test_edge_case_boundary_classification_mismatch():
    cols = [("customer_id", "VARCHAR"), ("amount", "DOUBLE")]
    src_sample = [{"customer_id": "C1", "amount": 500.00}]
    tgt_sample = [{"customer_id": "C2", "amount": 500.00}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        benchmark_scenario={"scenario_name": "BOUNDARY_REFUND_001"},
    )

    res = EdgeCaseValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL


def test_edge_case_scenario_name_in_summary():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        benchmark_scenario={"scenario_name": "FLAGSHIP_001"},
    )

    res = EdgeCaseValidator().validate(ctx)
    assert "FLAGSHIP_001" in res.summary


def test_edge_case_no_scenario_default():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        benchmark_scenario=None,
    )

    res = EdgeCaseValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_edge_case_data_unavailable():
    src = ExecutionResult(
        execution_id="e1",
        query_hash="h",
        dataset_id="d",
        dataset_hash="dh",
        status=ExecutionStatus.SUCCESS,
        timestamp="",
        row_count=0,
        columns=[],
        sample_data=None,
    )
    ctx = ValidationContext(source_execution=src, target_execution=src)

    res = EdgeCaseValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.SKIPPED


def test_edge_case_score_bounds():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    res = EdgeCaseValidator().validate(ctx)
    assert 0.0 <= res.score <= 1.0


def test_edge_case_duration_recorded():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    res = EdgeCaseValidator().validate(ctx)
    assert res.duration_ms >= 0.0


def test_edge_case_check_name():
    assert EdgeCaseValidator().name == "EdgeCaseValidator"


def test_edge_case_evidence_truncated_false():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    res = EdgeCaseValidator().validate(ctx)
    assert res.evidence_truncated is False
