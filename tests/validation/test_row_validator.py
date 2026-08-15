"""Unit tests for RowValidator and relational comparison."""

from backend.execution.models import ColumnSchema, ExecutionResult, ExecutionStatus
from backend.validation.comparison.values import compare_values, is_null_equivalent
from backend.validation.context import ValidationContext
from backend.validation.models import ValidationCheckStatus, ValidationConfig
from backend.validation.validators.rows import RowValidator


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


def test_row_exact_match():
    cols = [("customer_id", "VARCHAR"), ("status", "VARCHAR"), ("amount", "DOUBLE")]
    sample = [
        {"customer_id": "C1", "status": "ACTIVE", "amount": 100.0},
        {"customer_id": "C2", "status": "PENDING", "amount": 200.0},
    ]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        config=ValidationConfig(comparison_key=["customer_id"]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS
    assert res.mismatch_count == 0
    assert res.score == 1.0


def test_row_missing_key_in_target():
    cols = [("customer_id", "VARCHAR"), ("val", "INT")]
    src_sample = [{"customer_id": "C1", "val": 10}, {"customer_id": "C2", "val": 20}]
    tgt_sample = [{"customer_id": "C1", "val": 10}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        config=ValidationConfig(comparison_key=["customer_id"]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.mismatch_count == 1
    assert res.evidence[0].category == "MISSING_FROM_TARGET"


def test_row_extra_key_in_target():
    cols = [("customer_id", "VARCHAR"), ("val", "INT")]
    src_sample = [{"customer_id": "C1", "val": 10}]
    tgt_sample = [{"customer_id": "C1", "val": 10}, {"customer_id": "C2", "val": 20}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        config=ValidationConfig(comparison_key=["customer_id"]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.mismatch_count == 1
    assert res.evidence[0].category == "EXTRA_IN_TARGET"


def test_row_value_mismatch():
    cols = [("customer_id", "VARCHAR"), ("risk", "VARCHAR")]
    src_sample = [{"customer_id": "C1", "risk": "NORMAL"}]
    tgt_sample = [{"customer_id": "C1", "risk": "HIGH_RISK"}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        config=ValidationConfig(comparison_key=["customer_id"]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.evidence[0].category == "VALUE_MISMATCH"
    assert res.evidence[0].source_value == "NORMAL"
    assert res.evidence[0].target_value == "HIGH_RISK"


def test_row_multiple_mismatch_columns():
    cols = [("customer_id", "VARCHAR"), ("col1", "INT"), ("col2", "INT")]
    src_sample = [{"customer_id": "C1", "col1": 10, "col2": 20}]
    tgt_sample = [{"customer_id": "C1", "col1": 11, "col2": 22}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        config=ValidationConfig(comparison_key=["customer_id"]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.mismatch_count == 2


def test_row_missing_comparison_key_returns_error():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        config=ValidationConfig(comparison_key=[]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.ERROR


def test_row_invalid_key_returns_error():
    cols = [("customer_id", "VARCHAR")]
    sample = [{"customer_id": "C1"}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        config=ValidationConfig(comparison_key=["non_existent_key"]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.ERROR


def test_row_duplicate_key_warning():
    cols = [("customer_id", "VARCHAR"), ("val", "INT")]
    sample = [{"customer_id": "C1", "val": 10}, {"customer_id": "C1", "val": 10}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        config=ValidationConfig(comparison_key=["customer_id"]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS
    assert res.metadata["duplicate_key_warnings"] > 0


def test_value_comparison_null_vs_null():
    both, one = is_null_equivalent(None, None)
    assert both is True
    assert compare_values(None, None) is True


def test_value_comparison_null_vs_value():
    both, one = is_null_equivalent(None, "val")
    assert one is True
    assert compare_values(None, "val") is False


def test_value_comparison_float_tolerance():
    assert compare_values(100.0000001, 100.0000002, abs_tol=1e-5) is True
    assert compare_values(100.0, 105.0, abs_tol=1e-5) is False


def test_value_comparison_string_case():
    assert compare_values("ACTIVE", "ACTIVE") is True
    assert compare_values("ACTIVE", "active") is False


def test_row_composite_key():
    cols = [("c_id", "VARCHAR"), ("a_id", "VARCHAR"), ("bal", "DOUBLE")]
    sample = [{"c_id": "C1", "a_id": "A1", "bal": 50.0}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
        config=ValidationConfig(comparison_key=["c_id", "a_id"]),
    )

    res = RowValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_row_evidence_limit():
    cols = [("customer_id", "VARCHAR"), ("val", "INT")]
    src_sample = [{"customer_id": f"C{i}", "val": 1} for i in range(120)]
    tgt_sample = [{"customer_id": f"C{i}", "val": 2} for i in range(120)]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        config=ValidationConfig(comparison_key=["customer_id"], max_evidence_items=50),
    )

    res = RowValidator().validate(ctx)
    assert len(res.evidence) == 50
    assert res.evidence_truncated is True
    assert res.mismatch_count == 120
