"""Unit tests verifying all 12 pre-execution candidate integrity checks in CandidateRepairValidator."""

from backend.diagnosis_ai.models import RepairProposal, RepairStatus
from backend.repair_verification.candidate_validator import CandidateRepairValidator


def _build_valid_proposal() -> RepairProposal:
    return RepairProposal(
        repair_id="rep-001",
        discrepancy_id="D-001",
        status=RepairStatus.PROPOSED,
        original_sql="SELECT customer_id, refund_amount FROM transactions WHERE refund_amount >= 500;",
        proposed_sql="SELECT customer_id, refund_amount FROM transactions WHERE refund_amount > 500;",
        changed_region="where_clause",
    )


def test_check_1_status_must_be_proposed():
    prop = _build_valid_proposal()
    prop.status = RepairStatus.FAILED
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason == "STATUS_NOT_PROPOSED"


def test_check_2_empty_proposed_sql_rejected():
    prop = _build_valid_proposal()
    prop.proposed_sql = "   "
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason == "EMPTY_PROPOSED_SQL"


def test_check_3_missing_original_sql_rejected():
    prop = _build_valid_proposal()
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, "")
    assert not valid
    assert reason == "MISSING_ORIGINAL_TARGET_SQL"


def test_check_4_unchanged_repair_sql_rejected():
    prop = _build_valid_proposal()
    prop.proposed_sql = prop.original_sql
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason == "UNCHANGED_REPAIR_SQL"


def test_check_5_stored_proposal_artifact_mismatch_rejected():
    prop = _build_valid_proposal()
    stored_sql = "SELECT customer_id FROM transactions WHERE refund_amount > 600;"
    valid, reason, _ = CandidateRepairValidator.validate_candidate(
        prop, prop.original_sql, stored_proposal_sql=stored_sql
    )
    assert not valid
    assert reason == "REPAIR_ARTIFACT_MISMATCH"


def test_check_6_sql_syntax_error_rejected():
    prop = _build_valid_proposal()
    prop.proposed_sql = "SELECT FROM WHERE WHERE;"
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason == "SQL_SYNTAX_ERROR"


def test_check_7_read_only_violation_rejected():
    prop = _build_valid_proposal()
    prop.proposed_sql = "DELETE FROM transactions WHERE refund_amount > 500;"
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason == "READ_ONLY_VIOLATION"


def test_check_8_contract_alias_mismatch_rejected():
    prop = _build_valid_proposal()
    prop.original_sql = "SELECT customer_id AS cid, refund_amount AS r_amt FROM transactions WHERE refund_amount >= 500;"
    prop.proposed_sql = "SELECT customer_id AS customer_identifier, refund_amount AS r_amt FROM transactions WHERE refund_amount > 500;"
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason == "CONTRACT_ALIAS_MISMATCH"


def test_check_9_scope_constraint_violation_rejected():
    prop = _build_valid_proposal()
    prop.changed_region = "columns[risk_class]"
    prop.original_sql = "SELECT customer_id FROM transactions INNER JOIN customers ON t.cid = c.cid WHERE amount >= 500;"
    prop.proposed_sql = "SELECT customer_id FROM transactions LEFT JOIN customers ON t.cid = c.cid WHERE amount > 500;"
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason == "SCOPE_CONSTRAINT_VIOLATION"


def test_check_10_missing_required_table_rejected():
    prop = _build_valid_proposal()
    prop.proposed_sql = "SELECT 1 AS num;"
    valid, reason, _ = CandidateRepairValidator.validate_candidate(
        prop, prop.original_sql, expected_tables=["transactions"]
    )
    assert not valid
    assert reason == "MISSING_REQUIRED_TABLE"


def test_check_11_unknown_discrepancy_mapping_rejected():
    prop = _build_valid_proposal()
    prop.discrepancy_id = ""
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason == "UNKNOWN_DISCREPANCY_MAPPING"


def test_check_12_schema_inconsistency_rejected():
    prop = _build_valid_proposal()
    prop.proposed_sql = "SET schema = 'public';"
    valid, reason, _ = CandidateRepairValidator.validate_candidate(prop, prop.original_sql)
    assert not valid
    assert reason in ("READ_ONLY_VIOLATION", "SCHEMA_INCONSISTENCY")


def test_valid_candidate_passes_all_12_checks():
    prop = _build_valid_proposal()
    valid, reason, details = CandidateRepairValidator.validate_candidate(
        prop, prop.original_sql, stored_proposal_sql=prop.proposed_sql
    )
    assert valid
    assert reason == "CANDIDATE_ACCEPTED"
    assert details["checks_passed"] == 12
