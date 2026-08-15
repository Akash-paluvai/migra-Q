"""Unit tests for validation reproducibility and the 6 flagship validation scenarios."""

import pytest

from backend.analyzer.service import AnalyzerService
from backend.execution.models import ExecutionRequest
from backend.execution.service import ExecutionService
from backend.validation.models import ValidationConfig
from backend.validation.service import ValidationService


@pytest.fixture
def test_dataset_id():
    import argparse

    from backend.lab.cli import cmd_generate

    out_dir = "datasets/generated/test_exec"
    cmd_generate(argparse.Namespace(profile="test", seed=42, out_dir=out_dir, csv=False))
    return "test_exec"


# SCENARIO 1 — EXACT MATCH
def test_scenario_1_exact_match(test_dataset_id):
    sql = "SELECT customer_id, annual_income FROM customers WHERE annual_income > 50000"
    e1 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql, dataset_id=test_dataset_id))

    a1 = AnalyzerService.analyze(sql)
    a2 = AnalyzerService.analyze(sql)

    report = ValidationService.validate_executions(e1.execution_id, e2.execution_id, a1, a2)

    assert report.overall_status == "PASS"
    for chk in report.checks:
        assert chk.status in ("PASS", "SKIPPED")


# SCENARIO 2 — BOUNDARY BUG
def test_scenario_2_boundary_bug(test_dataset_id):
    sql_src = (
        "SELECT customer_id, amount, CASE WHEN amount > 500 THEN 'HIGH_RISK' "
        "ELSE 'NORMAL' END AS risk FROM transactions"
    )
    sql_tgt = (
        "SELECT customer_id, amount, CASE WHEN amount >= 500 THEN 'HIGH_RISK' "
        "ELSE 'NORMAL' END AS risk FROM transactions"
    )

    e1 = ExecutionService.execute(ExecutionRequest(sql=sql_src, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql_tgt, dataset_id=test_dataset_id))

    a1 = AnalyzerService.analyze(sql_src)
    a2 = AnalyzerService.analyze(sql_tgt)

    report = ValidationService.validate_executions(
        e1.execution_id,
        e2.execution_id,
        a1,
        a2,
        benchmark_scenario={"scenario_name": "BOUNDARY_REFUND_001"},
    )

    assert report.overall_status == "FAIL"
    # Business rule validator must detect boundary condition difference
    rule_chk = next(c for c in report.checks if c.check_name == "BusinessRuleValidator")
    assert rule_chk.status == "FAIL"


# SCENARIO 3 — NULL HANDLING DIFFERENCE
def test_scenario_3_null_handling_difference(test_dataset_id):
    sql_src = "SELECT account_id, closed_at FROM accounts WHERE closed_at IS NULL"
    sql_tgt = "SELECT account_id, closed_at FROM accounts WHERE closed_at = '9999-12-31'"

    e1 = ExecutionService.execute(ExecutionRequest(sql=sql_src, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql_tgt, dataset_id=test_dataset_id))

    a1 = AnalyzerService.analyze(sql_src)
    a2 = AnalyzerService.analyze(sql_tgt)

    report = ValidationService.validate_executions(
        e1.execution_id,
        e2.execution_id,
        a1,
        a2,
        config=ValidationConfig(comparison_key=["account_id"]),
    )

    assert report.overall_status == "FAIL"


# SCENARIO 4 — JOIN SEMANTICS DIFFERENCE
def test_scenario_4_join_semantics_difference(test_dataset_id):
    sql_src = (
        "SELECT c.customer_id, a.account_id FROM customers c "
        "JOIN accounts a ON c.customer_id = a.customer_id"
    )
    sql_tgt = (
        "SELECT c.customer_id, a.account_id FROM customers c "
        "LEFT JOIN accounts a ON c.customer_id = a.customer_id"
    )

    e1 = ExecutionService.execute(ExecutionRequest(sql=sql_src, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql_tgt, dataset_id=test_dataset_id))

    a1 = AnalyzerService.analyze(sql_src)
    a2 = AnalyzerService.analyze(sql_tgt)

    report = ValidationService.validate_executions(e1.execution_id, e2.execution_id, a1, a2)

    assert report.overall_status == "FAIL"
    rule_chk = next(c for c in report.checks if c.check_name == "BusinessRuleValidator")
    assert any(e.category == "JOIN_TYPE_CHANGED" for e in rule_chk.evidence)


# SCENARIO 5 — AGGREGATION DIFFERENCE
def test_scenario_5_aggregation_difference(test_dataset_id):
    sql_src = "SELECT customer_id, SUM(amount) AS total FROM transactions GROUP BY customer_id"
    sql_tgt = (
        "SELECT customer_id, SUM(DISTINCT amount) AS total FROM transactions GROUP BY customer_id"
    )

    e1 = ExecutionService.execute(ExecutionRequest(sql=sql_src, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql_tgt, dataset_id=test_dataset_id))

    a1 = AnalyzerService.analyze(sql_src)
    a2 = AnalyzerService.analyze(sql_tgt)

    report = ValidationService.validate_executions(e1.execution_id, e2.execution_id, a1, a2)

    assert report.overall_status == "FAIL"


# SCENARIO 6 — MISSING FILTER
def test_scenario_6_missing_filter(test_dataset_id):
    sql_src = "SELECT customer_id, amount FROM transactions WHERE status = 'COMPLETED'"
    sql_tgt = "SELECT customer_id, amount FROM transactions"

    e1 = ExecutionService.execute(ExecutionRequest(sql=sql_src, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql_tgt, dataset_id=test_dataset_id))

    a1 = AnalyzerService.analyze(sql_src)
    a2 = AnalyzerService.analyze(sql_tgt)

    report = ValidationService.validate_executions(e1.execution_id, e2.execution_id, a1, a2)

    assert report.overall_status == "FAIL"


# REPRODUCIBILITY TEST
def test_validation_reproducibility(test_dataset_id):
    sql_src = "SELECT customer_id, amount FROM transactions WHERE amount > 100"
    sql_tgt = "SELECT customer_id, amount FROM transactions WHERE amount >= 100"

    e1 = ExecutionService.execute(ExecutionRequest(sql=sql_src, dataset_id=test_dataset_id))
    e2 = ExecutionService.execute(ExecutionRequest(sql=sql_tgt, dataset_id=test_dataset_id))

    a1 = AnalyzerService.analyze(sql_src)
    a2 = AnalyzerService.analyze(sql_tgt)

    report1 = ValidationService.validate_executions(e1.execution_id, e2.execution_id, a1, a2)
    report2 = ValidationService.validate_executions(e1.execution_id, e2.execution_id, a1, a2)

    assert report1.overall_status == report2.overall_status
    assert report1.summary == report2.summary
    assert len(report1.checks) == len(report2.checks)

    for c1, c2 in zip(report1.checks, report2.checks):
        assert c1.check_name == c2.check_name
        assert c1.status == c2.status
        assert c1.score == c2.score
        assert c1.mismatch_count == c2.mismatch_count
        assert len(c1.evidence) == len(c2.evidence)

    # Validation IDs and creation timestamps differ as expected
    assert report1.validation_id != report2.validation_id
