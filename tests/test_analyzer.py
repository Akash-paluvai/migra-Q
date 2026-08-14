"""Comprehensive analyzer tests — 20 tests covering all extraction types,
edge cases, unsupported constructs, and deterministic metadata."""

import json

import pytest

from backend.analyzer.ast_diff import DiffCategory, compare_analyses
from backend.analyzer.service import analyze
from backend.core.exceptions import ParserError

# ── Basic parsing ───────────────────────────────────────────────────────────


def test_simple_select():
    r = analyze("SELECT id, name FROM users", dialect="teradata")
    assert len(r.tables) == 1
    assert r.tables[0].name == "users"
    assert {c.name for c in r.columns} >= {"id", "name"}


def test_empty_sql_raises():
    with pytest.raises(ParserError, match="Empty SQL input"):
        analyze("")


def test_invalid_sql_raises():
    with pytest.raises(ParserError):
        analyze("NOT A VALID SQL STATEMENT AT ALL !!!", dialect="teradata")


# ── Table extraction ───────────────────────────────────────────────────────


def test_multiple_tables_with_aliases():
    sql = "SELECT t.id FROM transactions AS t INNER JOIN customers AS c ON t.cid = c.id"
    r = analyze(sql)
    names = {t.name for t in r.tables}
    assert "transactions" in names
    assert "customers" in names
    aliases = {t.alias for t in r.tables if t.alias}
    assert "t" in aliases
    assert "c" in aliases


# ── Join extraction ────────────────────────────────────────────────────────


def test_inner_join():
    sql = "SELECT * FROM a INNER JOIN b ON a.id = b.aid"
    r = analyze(sql)
    assert len(r.joins) == 1
    assert r.joins[0].join_type == "INNER"
    assert "a.id" in r.joins[0].condition


def test_left_join():
    sql = "SELECT * FROM a LEFT JOIN b ON a.id = b.aid"
    r = analyze(sql)
    assert len(r.joins) == 1
    assert "LEFT" in r.joins[0].join_type


def test_multiple_joins():
    sql = """
    SELECT * FROM a
    INNER JOIN b ON a.id = b.aid
    LEFT JOIN c ON b.id = c.bid
    """
    r = analyze(sql)
    assert len(r.joins) == 2


# ── Filter extraction ──────────────────────────────────────────────────────


def test_where_filter():
    sql = "SELECT * FROM orders WHERE status = 'ACTIVE'"
    r = analyze(sql)
    assert len(r.filters) >= 1
    assert any("ACTIVE" in f.expression for f in r.filters)


def test_having_filter():
    sql = "SELECT cid, SUM(amt) FROM orders GROUP BY cid HAVING SUM(amt) > 1000"
    r = analyze(sql)
    having_filters = [f for f in r.filters if f.scope == "HAVING"]
    assert len(having_filters) >= 1


def test_compound_where():
    sql = "SELECT * FROM t WHERE a = 1 AND b = 2"
    r = analyze(sql)
    assert len(r.filters) >= 2


# ── Aggregation extraction ─────────────────────────────────────────────────


def test_sum_aggregation():
    sql = "SELECT SUM(amount) FROM transactions"
    r = analyze(sql)
    assert len(r.aggregations) >= 1
    assert r.aggregations[0].function == "SUM"


def test_count_distinct():
    sql = "SELECT COUNT(DISTINCT customer_id) FROM transactions"
    r = analyze(sql)
    assert len(r.aggregations) >= 1
    assert r.aggregations[0].function == "COUNT"
    assert r.aggregations[0].distinct is True


def test_group_by_captured():
    sql = "SELECT cid, SUM(amt) FROM orders GROUP BY cid"
    r = analyze(sql)
    assert len(r.aggregations) >= 1
    assert len(r.aggregations[0].group_by) >= 1


# ── CASE / Business rules ──────────────────────────────────────────────────


def test_case_expression_extraction():
    sql = """
    SELECT CASE WHEN score > 700 THEN 'GOOD' ELSE 'BAD' END FROM customers
    """
    r = analyze(sql)
    assert len(r.case_expressions) >= 1
    assert len(r.business_rules) >= 1
    assert r.business_rules[0].then == "'GOOD'"


def test_multi_when_case():
    sql = """
    SELECT CASE
        WHEN tier = 'A' THEN 1
        WHEN tier = 'B' THEN 2
        ELSE 3
    END FROM t
    """
    r = analyze(sql)
    assert len(r.case_expressions[0].whens) == 2
    assert len(r.business_rules) >= 2


# ── NULL-sensitive expressions ──────────────────────────────────────────────


def test_coalesce_detected():
    sql = "SELECT COALESCE(amount, 0) FROM t"
    r = analyze(sql)
    assert len(r.null_sensitive_expressions) >= 1
    assert any(n.kind == "COALESCE" for n in r.null_sensitive_expressions)


# ── Unsupported constructs emit warnings ────────────────────────────────────


def test_subquery_warning():
    sql = "SELECT * FROM (SELECT id FROM t) AS sub"
    r = analyze(sql)
    unsupported = [w for w in r.warnings if w.code == "UNSUPPORTED_CONSTRUCT"]
    assert len(unsupported) >= 1, "Subquery should trigger UNSUPPORTED_CONSTRUCT warning"


# ── Deterministic metadata ─────────────────────────────────────────────────


def test_sql_hash_deterministic():
    sql = "SELECT id FROM users WHERE active = 1"
    r1 = analyze(sql)
    r2 = analyze(sql)
    assert r1.sql_hash == r2.sql_hash


def test_analyzer_version_present():
    r = analyze("SELECT 1")
    assert r.analyzer_version == "0.1.0"


# ── JSON serialisation round-trip ───────────────────────────────────────────


def test_json_roundtrip():
    r = analyze("SELECT SUM(x) FROM t WHERE a = 1 GROUP BY b")
    d = r.model_dump()
    j = json.dumps(d, default=str)
    loaded = json.loads(j)
    assert loaded["dialect"]
    assert loaded["sql_hash"]


# ── AST diff ────────────────────────────────────────────────────────────────


def test_identical_analyses_no_diffs():
    sql = "SELECT id FROM t"
    a = analyze(sql)
    b = analyze(sql)
    diff = compare_analyses(a, b)
    assert diff.is_identical


def test_join_type_diff():
    src = analyze("SELECT * FROM a INNER JOIN b ON a.id = b.aid")
    tgt = analyze("SELECT * FROM a LEFT JOIN b ON a.id = b.aid")
    diff = compare_analyses(src, tgt)
    assert not diff.is_identical
    cats = {d.category for d in diff.diffs}
    assert DiffCategory.JOIN_TYPE_CHANGED in cats


def test_filter_diff():
    src = analyze("SELECT * FROM t WHERE x > 500")
    tgt = analyze("SELECT * FROM t WHERE x >= 500")
    diff = compare_analyses(src, tgt)
    assert not diff.is_identical


# ── Flagship customer_risk.sql ──────────────────────────────────────────────


def test_customer_risk_fixture():
    from pathlib import Path

    sql_path = Path(__file__).resolve().parent.parent / "examples" / "customer_risk.sql"
    if not sql_path.exists():
        pytest.skip("examples/customer_risk.sql not found")
    sql = sql_path.read_text()
    r = analyze(sql)
    assert len(r.tables) >= 2
    assert len(r.joins) >= 1
    assert len(r.filters) >= 1
    assert len(r.aggregations) >= 1
    assert len(r.business_rules) >= 1
