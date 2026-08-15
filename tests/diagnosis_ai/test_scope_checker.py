"""Unit tests for AST RepairScopeChecker verifying minimal repair scope enforcement."""

from backend.diagnosis_ai.scope import RepairScopeChecker


def test_minimal_repair_scope_passes():
    orig_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

    prop_sql = """SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;"""

    valid, msg, constraints = RepairScopeChecker.verify_repair_scope(
        orig_sql, prop_sql, "bigquery", "columns[risk_class]"
    )
    assert valid is True
    assert "AST Scope Check passed" in msg
    assert "join_clause_unchanged" in constraints
    assert "groupby_clause_unchanged" in constraints


def test_scope_creep_rejected_on_join_modification():
    orig_sql = """SELECT c.customer_id,
  CASE WHEN t.amount >= 500 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t JOIN customers c ON t.customer_id = c.customer_id;"""

    # Creep: LEFT JOIN introduced unnecessarily!
    creep_sql = """SELECT c.customer_id,
  CASE WHEN t.amount > 500 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t LEFT JOIN customers c ON t.customer_id = c.customer_id;"""

    valid, msg, _ = RepairScopeChecker.verify_repair_scope(
        orig_sql, creep_sql, "bigquery", "columns[risk_class]"
    )
    assert valid is False
    assert "UNJUSTIFIED_SCOPE_CHANGE: Repair modified JOIN clause" in msg


def test_wrong_discrepancy_repair_rejected_on_unrelated_projection_change():
    orig_sql = """SELECT c.customer_id, SUM(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.customer_id, t.amount;"""

    # Wrong repair: Modifies SUM(t.amount) to COUNT(t.amount) when discrepancy target is risk_class!
    wrong_sql = """SELECT c.customer_id, COUNT(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t JOIN customers c ON t.customer_id = c.customer_id
GROUP BY c.customer_id, t.amount;"""

    valid, msg, _ = RepairScopeChecker.verify_repair_scope(
        orig_sql, wrong_sql, "bigquery", "columns[risk_class]"
    )
    assert valid is False
    assert "UNJUSTIFIED_SCOPE_CHANGE: Repair modified projection expression" in msg
