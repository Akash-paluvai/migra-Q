import pytest
from backend.preflight.validator import SchemaPreflightValidator

def test_real_registry_semantic_resolution_pass():
    """
    Test that a valid query using aliases and complex clauses
    passes semantic resolution against the REAL dataset registry objects
    (without mocks), proving the ColumnSchema -> sqlglot schema mapping works.
    """
    sql = """
    SELECT
        department,
        COUNT(*) AS metric_count,
        SUM(score) AS total_score,
        AVG(score) AS avg_score,
        COALESCE(AVG(score), 0) AS avg_score_default,
        CASE
            WHEN AVG(score) >= 75 THEN 'HIGH'
            WHEN AVG(score) >= 50 THEN 'MEDIUM'
            ELSE 'LOW'
        END AS performance_band
    FROM enterprise_metrics
    GROUP BY department
    QUALIFY AVG(score) > 40
    ORDER BY avg_score DESC;
    """
    
    # "enterprise_metrics" dataset has the "enterprise_metrics" table in this environment.
    # Note: If it doesn't, this test will fail correctly.
    result = SchemaPreflightValidator.validate(sql, dataset_id="enterprise_metrics", dialect="teradata")
    
    assert result.status == "PASS"
    assert result.execution_allowed is True


def test_real_registry_missing_column_blocked():
    """
    Test that a query referencing an explicitly missing column
    in the real dataset correctly yields INPUT_SCHEMA_MISMATCH.
    """
    sql = """
    SELECT t.refund_amount
    FROM transactions t;
    """
    
    result = SchemaPreflightValidator.validate(sql, dataset_id="customer_risk", dialect="teradata")
    
    assert result.status == "FAILED"
    assert result.failure_category == "INPUT_SCHEMA_MISMATCH"
    assert "refund_amount" in result.reason
