"""Unit tests for SchemaValidator."""

from backend.execution.models import ColumnSchema, ExecutionResult, ExecutionStatus
from backend.validation.context import ValidationContext
from backend.validation.models import ValidationCheckStatus, ValidationConfig
from backend.validation.validators.schema import SchemaValidator


def make_execution(cols):
    return ExecutionResult(
        execution_id="exec-1",
        query_hash="h1",
        dataset_id="d1",
        dataset_hash="dh1",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T00:00:00Z",
        row_count=10,
        columns=[ColumnSchema(name=n, type=t) for n, t in cols],
    )


def test_schema_exact_match():
    cols = [("id", "VARCHAR"), ("val", "DOUBLE")]
    ctx = ValidationContext(
        source_execution=make_execution(cols), target_execution=make_execution(cols)
    )

    res = SchemaValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS
    assert res.score == 1.0
    assert res.mismatch_count == 0


def test_schema_missing_column():
    src = make_execution([("id", "VARCHAR"), ("extra", "INT")])
    tgt = make_execution([("id", "VARCHAR")])
    ctx = ValidationContext(source_execution=src, target_execution=tgt)

    res = SchemaValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.mismatch_count == 1
    assert res.evidence[0].category == "COLUMN_MISSING"
    assert res.evidence[0].column == "extra"


def test_schema_extra_column():
    src = make_execution([("id", "VARCHAR")])
    tgt = make_execution([("id", "VARCHAR"), ("new_col", "INT")])
    ctx = ValidationContext(source_execution=src, target_execution=tgt)

    res = SchemaValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.mismatch_count == 1
    assert res.evidence[0].category == "COLUMN_EXTRA"


def test_schema_type_changed():
    src = make_execution([("id", "VARCHAR"), ("score", "DOUBLE")])
    tgt = make_execution([("id", "VARCHAR"), ("score", "VARCHAR")])
    ctx = ValidationContext(source_execution=src, target_execution=tgt)

    res = SchemaValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.evidence[0].category == "TYPE_CHANGED"


def test_schema_type_normalization_equivalent():
    src = make_execution([("id", "VARCHAR")])
    tgt = make_execution([("id", "STRING")])
    ctx = ValidationContext(source_execution=src, target_execution=tgt)

    res = SchemaValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_schema_column_order_mismatch():
    src = make_execution([("a", "INT"), ("b", "INT")])
    tgt = make_execution([("b", "INT"), ("a", "INT")])
    ctx = ValidationContext(
        source_execution=src,
        target_execution=tgt,
        config=ValidationConfig(schema_column_order_matters=True),
    )

    res = SchemaValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.evidence[0].category == "COLUMN_ORDER_CHANGED"


def test_schema_column_order_ignored_when_configured():
    src = make_execution([("a", "INT"), ("b", "INT")])
    tgt = make_execution([("b", "INT"), ("a", "INT")])
    ctx = ValidationContext(
        source_execution=src,
        target_execution=tgt,
        config=ValidationConfig(schema_column_order_matters=False),
    )

    res = SchemaValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_schema_empty_columns():
    src = make_execution([])
    tgt = make_execution([])
    ctx = ValidationContext(source_execution=src, target_execution=tgt)

    res = SchemaValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS
