"""Unit tests verifying RepairProposalValidator syntax, read-only safety, and contract check."""

from backend.diagnosis_ai.validator import RepairProposalValidator


def test_valid_repair_syntax_and_safety_passes():
    sql = "SELECT customer_id, risk_class FROM transactions WHERE amount > 500;"
    valid, msg = RepairProposalValidator.validate_repair_syntax_and_safety(sql, "bigquery")
    assert valid is True
    assert "syntactically valid and read-only" in msg


def test_mutating_repair_blocked():
    sql = "DROP TABLE customers;"
    valid, msg = RepairProposalValidator.validate_repair_syntax_and_safety(sql, "bigquery")
    assert valid is False
    assert "violates read-only safety policy" in msg


def test_repair_contract_check_passes():
    orig_sql = "SELECT customer_id, risk_class FROM transactions;"
    prop_sql = "SELECT customer_id, risk_class FROM transactions;"

    valid, msg = RepairProposalValidator.validate_target_contract(orig_sql, prop_sql, "bigquery")
    assert valid is True
    assert "Target contract preserved" in msg


def test_repair_contract_check_fails_on_alias_change():
    orig_sql = "SELECT customer_id, risk_class FROM transactions;"
    prop_sql = "SELECT customer_id, risk_score FROM transactions;"  # Output alias changed!

    valid, msg = RepairProposalValidator.validate_target_contract(orig_sql, prop_sql, "bigquery")
    assert valid is False
    assert "REPAIR_CONTRACT_CHECK VIOLATION: Output column aliases changed" in msg
