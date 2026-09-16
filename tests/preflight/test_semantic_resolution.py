import pytest
from unittest.mock import patch, MagicMock

from backend.preflight.validator import SchemaPreflightValidator

@pytest.fixture
def mock_dataset_registry():
    with patch("backend.preflight.semantic.DatasetRegistry") as MockRegistry:
        mock_registry = MockRegistry.return_value
        
        mock_dataset = MagicMock()
        
        # We need mock table summaries
        class MockColumn:
            def __init__(self, name, data_type):
                self.name = name
                self.data_type = data_type
                
        class MockTableSummary:
            def __init__(self, name, columns):
                self.table_name = name
                self.columns = columns
                
        mock_dataset.table_summaries = [
            MockTableSummary("enterprise_metrics", [
                MockColumn("metric_id", "INT"),
                MockColumn("department", "VARCHAR"),
                MockColumn("score", "FLOAT"),
                MockColumn("gate_status", "VARCHAR")
            ]),
            MockTableSummary("transactions", [
                MockColumn("transaction_id", "INT"),
                MockColumn("customer_id", "INT"),
                MockColumn("amount", "FLOAT"),
                MockColumn("status", "VARCHAR"),
                MockColumn("timestamp", "TIMESTAMP")
            ]),
            MockTableSummary("customers", [
                MockColumn("customer_id", "INT"),
                MockColumn("name", "VARCHAR")
            ])
        ]
        
        mock_registry.get_dataset.return_value = mock_dataset
        yield mock_registry

def test_physical_column(mock_dataset_registry):
    sql = "SELECT score FROM enterprise_metrics;"
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "PASS"

def test_select_alias(mock_dataset_registry):
    sql = "SELECT AVG(score) AS avg_score FROM enterprise_metrics ORDER BY avg_score DESC;"
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "PASS"

def test_another_alias(mock_dataset_registry):
    sql = "SELECT SUM(score) AS total_score FROM enterprise_metrics ORDER BY total_score DESC;"
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "PASS"

def test_genuine_missing_column(mock_dataset_registry):
    sql = "SELECT refund_amount FROM enterprise_metrics;"
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "FAILED"
    assert result.failure_category == "INPUT_SCHEMA_MISMATCH"
    assert "refund_amount" in result.reason

def test_qualified_missing_column(mock_dataset_registry):
    sql = "SELECT t.refund_amount FROM transactions t;"
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "FAILED"
    assert result.failure_category == "INPUT_SCHEMA_MISMATCH"
    assert "refund_amount" in result.reason

def test_unknown_order_by_identifier(mock_dataset_registry):
    sql = "SELECT AVG(score) AS avg_score FROM enterprise_metrics ORDER BY nonexistent_column;"
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "FAILED"
    assert "nonexistent_column" in result.reason

def test_cte_resolution(mock_dataset_registry):
    sql = """
    WITH metrics AS (
        SELECT department, AVG(score) AS avg_score
        FROM enterprise_metrics
        GROUP BY department
    )
    SELECT department, avg_score
    FROM metrics;
    """
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "PASS"

def test_subquery_resolution(mock_dataset_registry):
    sql = """
    SELECT x.avg_score
    FROM (
        SELECT AVG(score) AS avg_score
        FROM enterprise_metrics
    ) x;
    """
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "PASS"

def test_join_ambiguity(mock_dataset_registry):
    sql = """
    SELECT customer_id
    FROM customers c
    JOIN transactions t
      ON c.customer_id = t.customer_id;
    """
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "FAILED"
    assert "customer_id" in result.reason

def test_qualified_join(mock_dataset_registry):
    sql = """
    SELECT c.customer_id
    FROM customers c
    JOIN transactions t
      ON c.customer_id = t.customer_id;
    """
    result = SchemaPreflightValidator.validate(sql, "test_dataset")
    assert result.status == "PASS"
