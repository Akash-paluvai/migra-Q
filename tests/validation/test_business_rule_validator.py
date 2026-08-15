"""Unit tests for BusinessRuleValidator."""

from backend.analyzer.service import AnalyzerService
from backend.execution.models import ExecutionResult, ExecutionStatus
from backend.validation.context import ValidationContext
from backend.validation.models import ValidationCheckStatus
from backend.validation.validators.business_rules import BusinessRuleValidator


def make_exec():
    return ExecutionResult(
        execution_id="exec-1",
        query_hash="h1",
        dataset_id="d1",
        dataset_hash="dh1",
        status=ExecutionStatus.SUCCESS,
        timestamp="2026-08-15T00:00:00Z",
        row_count=10,
        columns=[],
    )


def test_business_rule_identical_analysis():
    sql = "SELECT * FROM customers"
    ana = AnalyzerService.analyze(sql)
    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=ana,
        target_analysis=ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS
    assert res.mismatch_count == 0


def test_business_rule_missing_analysis_skipped():
    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=None,
        target_analysis=None,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.SKIPPED


def test_scenario_2_boundary_bug_operator_difference():
    sql_src = (
        "SELECT customer_id, amount, CASE WHEN amount > 500 THEN 'HIGH_RISK' "
        "ELSE 'NORMAL' END AS risk FROM transactions"
    )
    sql_tgt = (
        "SELECT customer_id, amount, CASE WHEN amount >= 500 THEN 'HIGH_RISK' "
        "ELSE 'NORMAL' END AS risk FROM transactions"
    )

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert res.mismatch_count > 0


def test_business_rule_join_type_difference():
    sql_src = (
        "SELECT c.customer_id, a.account_id FROM customers c "
        "JOIN accounts a ON c.customer_id = a.customer_id"
    )
    sql_tgt = (
        "SELECT c.customer_id, a.account_id FROM customers c "
        "LEFT JOIN accounts a ON c.customer_id = a.customer_id"
    )

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert any(e.category == "JOIN_TYPE_CHANGED" for e in res.evidence)


def test_business_rule_filter_added():
    sql_src = "SELECT * FROM transactions"
    sql_tgt = "SELECT * FROM transactions WHERE status = 'ACTIVE'"

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert any(e.category == "FILTER_ADDED" for e in res.evidence)


def test_business_rule_filter_removed():
    sql_src = "SELECT * FROM transactions WHERE status = 'ACTIVE'"
    sql_tgt = "SELECT * FROM transactions"

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert any(e.category == "FILTER_REMOVED" for e in res.evidence)


def test_business_rule_null_sensitive_expression():
    sql_src = "SELECT account_id FROM accounts WHERE closed_at IS NULL"
    sql_tgt = "SELECT account_id FROM accounts WHERE closed_at = '9999-12-31'"

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert any(e.category == "NULL_SEMANTICS_CHANGED" for e in res.evidence)


def test_business_rule_score_bounds():
    ana1 = AnalyzerService.analyze("SELECT * FROM customers")
    ana2 = AnalyzerService.analyze("SELECT * FROM transactions")

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=ana1,
        target_analysis=ana2,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert 0.0 <= res.score <= 1.0


def test_business_rule_join_condition_changed():
    sql_src = (
        "SELECT c.customer_id, a.account_id FROM customers c "
        "JOIN accounts a ON c.customer_id = a.customer_id"
    )
    sql_tgt = (
        "SELECT c.customer_id, a.account_id FROM customers c "
        "JOIN accounts a ON c.customer_id = a.account_id"
    )

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL
    assert any(e.category == "JOIN_CONDITION_CHANGED" for e in res.evidence)


def test_business_rule_case_branch_count_diff():
    sql_src = "SELECT CASE WHEN amount > 500 THEN 'HIGH' ELSE 'LOW' END FROM transactions"
    sql_tgt = (
        "SELECT CASE WHEN amount > 500 THEN 'HIGH' WHEN amount > 200 THEN 'MEDIUM' "
        "ELSE 'LOW' END FROM transactions"
    )

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.FAIL


def test_business_rule_table_alias_diff():
    sql_src = "SELECT * FROM customers AS c"
    sql_tgt = "SELECT * FROM customers AS cust"

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.status == ValidationCheckStatus.PASS


def test_business_rule_duration_captured():
    ana = AnalyzerService.analyze("SELECT 1")
    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=ana,
        target_analysis=ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert res.duration_ms >= 0.0


def test_business_rule_diff_categories_in_metadata():
    sql_src = "SELECT * FROM transactions WHERE amount > 100"
    sql_tgt = "SELECT * FROM transactions WHERE amount > 200"

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    cats = [str(c) for c in res.metadata["diff_categories"]]
    assert "FILTER_ADDED" in cats or "DiffCategory.FILTER_ADDED" in cats


def test_business_rule_evidence_items_structured():
    sql_src = "SELECT * FROM transactions WHERE amount > 100"
    sql_tgt = "SELECT * FROM transactions WHERE amount >= 100"

    src_ana = AnalyzerService.analyze(sql_src)
    tgt_ana = AnalyzerService.analyze(sql_tgt)

    ctx = ValidationContext(
        source_execution=make_exec(),
        target_execution=make_exec(),
        source_analysis=src_ana,
        target_analysis=tgt_ana,
    )

    res = BusinessRuleValidator().validate(ctx)
    assert len(res.evidence) > 0
    assert res.evidence[0].source_value is not None


def test_business_rule_check_name():
    assert BusinessRuleValidator().name == "BusinessRuleValidator"
