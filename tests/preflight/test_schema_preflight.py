import pytest
from backend.preflight.validator import SchemaPreflightValidator

def test_valid_query_passes_preflight():
    sql = "SELECT customer_id, customer_segment FROM customers"
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk")
    assert result.status == "PASS"
    assert result.execution_allowed is True

def test_missing_column_blocks_execution():
    sql = "SELECT customer_id, refund_amount FROM transactions"
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk")
    assert result.status == "FAILED"
    assert result.failure_category == "INPUT_SCHEMA_MISMATCH"
    assert result.execution_allowed is False
    assert len(result.missing_columns) == 1
    assert result.missing_columns[0].column.lower() == "refund_amount"
    assert "transactions" in result.available_columns
    assert "transaction_id" in result.available_columns["transactions"]

def test_table_alias_is_resolved():
    sql = "SELECT t.transaction_id, t.fake_col FROM transactions t"
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk")
    assert result.status == "FAILED"
    assert result.execution_allowed is False
    assert result.missing_columns[0].table == "transactions"
    assert result.missing_columns[0].column.lower() == "fake_col"

def test_join_columns_are_resolved():
    sql = "SELECT c.customer_segment, SUM(t.amount) AS total_amount, NVL(SUM(t.refund_amount), 0) FROM transactions t INNER JOIN customers c ON t.customer_id = c.customer_id"
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk")
    assert result.status == "FAILED"
    assert result.execution_allowed is False
    assert result.missing_columns[0].table == "transactions"
    assert result.missing_columns[0].column.lower() == "refund_amount"

def test_multiple_missing_columns_are_reported():
    sql = "SELECT missing1, missing2 FROM transactions"
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk")
    assert result.status == "FAILED"
    assert len(result.missing_columns) == 2

def test_unknown_table_is_reported():
    sql = "SELECT * FROM missing_table"
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk")
    assert result.status == "FAILED"
    assert result.execution_allowed is False
    assert "missing_table" in result.unresolved_tables

def test_select_star_is_allowed():
    sql = "SELECT * FROM transactions"
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk")
    assert result.status == "PASS"

def test_function_arguments_are_not_false_positive_columns():
    sql = "SELECT EXTRACT(DAY FROM timestamp) FROM transactions"
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk")
    assert result.status == "PASS"
    assert result.execution_allowed is True
