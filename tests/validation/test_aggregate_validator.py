"""Unit tests for AggregateValidator."""

from backend.execution.models import ColumnSchema, ExecutionResult, ExecutionStatus
from backend.validation.context import ValidationContext
from backend.validation.models import ValidationCheckStatus, ValidationConfig
from backend.validation.validators.aggregates import AggregateValidator, _compute_stat


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


def test_aggregate_exact_match():
    cols = [("customer_id", "VARCHAR"), ("amount", "DOUBLE")]
    sample = [{"customer_id": "C1", "amount": 10.0}, {"customer_id": "C2", "amount": 20.0}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, sample),
        target_execution=make_exec_sample(cols, sample),
    )

    res = AggregateValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS
    assert res.score == 1.0


def test_aggregate_sum_mismatch():
    cols = [("customer_id", "VARCHAR"), ("amount", "DOUBLE")]
    src_sample = [{"customer_id": "C1", "amount": 10.0}, {"customer_id": "C2", "amount": 20.0}]
    tgt_sample = [{"customer_id": "C1", "amount": 10.0}, {"customer_id": "C2", "amount": 30.0}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
    )

    res = AggregateValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.mismatch_count > 0


def test_aggregate_count_mismatch():
    cols = [("customer_id", "VARCHAR")]
    src_sample = [{"customer_id": "C1"}, {"customer_id": "C2"}]
    tgt_sample = [{"customer_id": "C1"}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
    )

    res = AggregateValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL


def test_compute_stat_null_handling():
    import pandas as pd

    df = pd.DataFrame({"val": [10.0, None, 20.0]})

    assert _compute_stat(df, "val", "COUNT") == 2
    assert _compute_stat(df, "val", "SUM") == 30.0
    assert _compute_stat(df, "val", "AVG") == 15.0


def test_compute_stat_count_distinct():
    import pandas as pd

    df = pd.DataFrame({"cat": ["A", "A", "B"]})

    assert _compute_stat(df, "cat", "COUNT_DISTINCT") == 2


def test_aggregate_custom_spec():
    cols = [("val", "DOUBLE")]
    src_sample = [{"val": 10.0}, {"val": 20.0}]
    tgt_sample = [{"val": 10.0}, {"val": 20.0}]

    spec = [{"column": "val", "functions": ["SUM"]}]
    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        config=ValidationConfig(aggregate_specs=spec),
    )

    res = AggregateValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS
    assert res.metadata["total_aggregates"] == 1


def test_aggregate_numeric_tolerance():
    cols = [("amount", "DOUBLE")]
    src_sample = [{"amount": 100.0000001}]
    tgt_sample = [{"amount": 100.0000002}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
        config=ValidationConfig(numeric_absolute_tolerance=1e-5),
    )

    res = AggregateValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_aggregate_min_max_check():
    cols = [("amount", "DOUBLE")]
    src_sample = [{"amount": 10.0}, {"amount": 50.0}]
    tgt_sample = [{"amount": 10.0}, {"amount": 50.0}]

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
    )

    res = AggregateValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_aggregate_empty_df():
    cols = [("amount", "DOUBLE")]
    src_sample = []
    tgt_sample = []

    ctx = ValidationContext(
        source_execution=make_exec_sample(cols, src_sample),
        target_execution=make_exec_sample(cols, tgt_sample),
    )

    res = AggregateValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_aggregate_data_unavailable():
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

    res = AggregateValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.ERROR
