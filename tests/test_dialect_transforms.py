import pytest
import sqlglot
from sqlglot import expressions as exp
from backend.execution.dialect_transforms import transform_for_duckdb

def _transform(sql: str, read_dialect: str) -> str:
    parsed = sqlglot.parse_one(sql, read=read_dialect)
    transformed = parsed.transform(lambda node: transform_for_duckdb(node, read_dialect))
    return transformed.sql(dialect="duckdb")

# --- COMMON ---
def test_ast_transform_strip_project_dataset():
    """Catalog and dataset prefixes are stripped from tables."""
    sql = "SELECT * FROM `project.dataset.primary_entity`"
    res = _transform(sql, "bigquery")
    assert "project.dataset" not in res
    assert '"primary_entity"' in res or 'primary_entity' in res

# --- ORACLE ---
def test_oracle_keep_arg_max():
    """Oracle KEEP (DENSE_RANK LAST ORDER BY ... ASC) -> arg_max."""
    sql = "SELECT MAX(x) KEEP (DENSE_RANK LAST ORDER BY y ASC) FROM t"
    res = _transform(sql, "oracle")
    assert "ARG_MAX(X, Y)" in res.upper()
    
    # Also LAST ORDER BY ... (no direction defaults to ASC)
    sql = "SELECT MAX(x) KEEP (DENSE_RANK LAST ORDER BY y) FROM t"
    res = _transform(sql, "oracle")
    assert "ARG_MAX(X, Y)" in res.upper()
    
    # FIRST ORDER BY ... DESC
    sql = "SELECT MAX(x) KEEP (DENSE_RANK FIRST ORDER BY y DESC) FROM t"
    res = _transform(sql, "oracle")
    assert "ARG_MAX(X, Y)" in res.upper()

def test_oracle_keep_arg_min():
    """Oracle KEEP (DENSE_RANK LAST ORDER BY ... DESC) -> arg_min."""
    sql = "SELECT MAX(x) KEEP (DENSE_RANK LAST ORDER BY y DESC) FROM t"
    res = _transform(sql, "oracle")
    assert "ARG_MIN(X, Y)" in res.upper()
    
    # FIRST ORDER BY ... ASC
    sql = "SELECT MAX(x) KEEP (DENSE_RANK FIRST ORDER BY y ASC) FROM t"
    res = _transform(sql, "oracle")
    assert "ARG_MIN(X, Y)" in res.upper()

def test_oracle_ordinary_max_unchanged():
    """Oracle ordinary MAX/MIN should be unchanged."""
    sql = "SELECT MAX(x) FROM t"
    res = _transform(sql, "oracle")
    assert "MAX(X)" in res.upper()
    assert "KEEP" not in res.upper()

# --- BIGQUERY ---
def test_bigquery_array_agg_arg_max():
    """ARRAY_AGG(... DESC LIMIT 1) becomes arg_max."""
    sql = "(ARRAY_AGG(val ORDER BY order_col DESC LIMIT 1))[OFFSET(0)]"
    res = _transform(sql, "bigquery")
    assert "ARG_MAX(VAL, ORDER_COL)" in res.upper()

def test_bigquery_array_agg_arg_min():
    """ARRAY_AGG(... ASC LIMIT 1) becomes arg_min."""
    sql = "(ARRAY_AGG(val ORDER BY order_col ASC LIMIT 1))[OFFSET(0)]"
    res = _transform(sql, "bigquery")
    assert "ARG_MIN(VAL, ORDER_COL)" in res.upper()

def test_bigquery_ordinary_array_agg():
    """Ordinary ARRAY_AGG without LIMIT 1 should remain unaffected."""
    sql = "ARRAY_AGG(val)"
    res = _transform(sql, "bigquery")
    assert "ARRAY_AGG" in res.upper()
    assert "ARG_MAX" not in res.upper()

# --- TERADATA ---
def test_teradata_top():
    """Teradata TOP should map seamlessly (usually via standard transpilation to LIMIT)."""
    sql = "SELECT TOP 10 * FROM some_table"
    res = _transform(sql, "teradata")
    assert "LIMIT 10" in res.upper()

def test_teradata_qualify():
    """Teradata QUALIFY should map seamlessly."""
    sql = "SELECT * FROM some_table QUALIFY ROW_NUMBER() OVER (PARTITION BY ref_code ORDER BY entity_id) = 1"
    res = _transform(sql, "teradata")
    assert "QUALIFY ROW_NUMBER()" in res.upper()
    assert "PARTITION BY" in res.upper()

def test_teradata_ordinary_no_oracle_leak():
    """Teradata should not accidentally trigger Oracle or BigQuery transforms."""
    # A generic query with MAX
    sql = "SELECT MAX(x) FROM t"
    res = _transform(sql, "teradata")
    assert "MAX(X)" in res.upper()
