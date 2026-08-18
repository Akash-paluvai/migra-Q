"""Regression tests for causal linkage, downstream aggregates, and evidence isolation."""

from backend.diagnosis.evidence import EvidenceConsolidator
from backend.diagnosis.models import DiscrepancyCategory
from backend.diagnosis.signals import RawDiscrepancySignal


def test_regression_a_boundary_changes_only_classification():
    """A. Boundary discrepancy changes only classification (risk_class)."""
    sig_struct = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="columns[risk_class]",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        payload={"column": "risk_class"},
    )
    sig_row = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="columns[risk_class]",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        payload={
            "column": "risk_class",
            "mismatch_count": 229,
            "source_value": "NORMAL",
            "target_value": "HIGH_RISK",
        },
    )

    consolidator = EvidenceConsolidator()
    report = consolidator.consolidate("val-test-a", [sig_struct, sig_row], total_output_rows=10000)

    assert len(report) == 1
    disc = report[0]
    assert disc.category == DiscrepancyCategory.BOUNDARY_CONDITION
    assert disc.affected_row_count == 229
    assert disc.total_output_rows == 10000
    assert disc.affected_percentage == 2.29
    assert disc.affected_output_columns == ["risk_class"]
    assert disc.classification_confidence == 0.95


def test_regression_b_boundary_affects_downstream_aggregate():
    """B. Boundary discrepancy legitimately affects downstream aggregate."""
    sig_struct = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="columns[high_risk_total]",
        source_expression="SUM(CASE WHEN t.amount > 500 THEN t.amount ELSE 0 END)",
        target_expression="SUM(CASE WHEN t.amount >= 500 THEN t.amount ELSE 0 END)",
        payload={"column": "high_risk_total"},
    )
    sig_agg = RawDiscrepancySignal(
        source_validator="AggregateValidator",
        signal_type="AGGREGATE_MISMATCH",
        analysis_path="columns[high_risk_total]",
        source_expression="SUM(CASE WHEN t.amount > 500 THEN t.amount ELSE 0 END)",
        target_expression="SUM(CASE WHEN t.amount >= 500 THEN t.amount ELSE 0 END)",
        payload={
            "column": "high_risk_total",
            "mismatch_count": 1,
            "source_value": "50000.0",
            "target_value": "50500.0",
        },
    )

    consolidator = EvidenceConsolidator()
    report = consolidator.consolidate("val-test-b", [sig_struct, sig_agg], total_output_rows=1000)

    assert len(report) == 1
    disc = report[0]
    assert disc.category == DiscrepancyCategory.BOUNDARY_CONDITION
    assert disc.affected_output_columns == ["high_risk_total"]


def test_regression_c_two_unrelated_discrepancies_overlapping_rows():
    """C. Two unrelated discrepancies (boundary on risk_class vs date trunc on tx_date)."""
    sig_boundary = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="columns[risk_class]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={"column": "risk_class"},
    )
    sig_date = RawDiscrepancySignal(
        source_validator="AST_ANALYZER",
        signal_type="DATE_TRUNC_DIFF",
        analysis_path="columns[tx_date]",
        source_expression="DATE_TRUNC('month', created_at)",
        target_expression="DATE_TRUNC('day', created_at)",
        payload={"column": "tx_date"},
    )

    consolidator = EvidenceConsolidator()
    report = consolidator.consolidate(
        "val-test-c", [sig_boundary, sig_date], total_output_rows=1000
    )

    assert len(report) == 2
    cats = [d.category for d in report]
    assert DiscrepancyCategory.BOUNDARY_CONDITION in cats
    assert DiscrepancyCategory.DATE_SEMANTICS in cats


def test_regression_d_same_row_mismatch_different_rule_not_merged():
    """D. Same row mismatch caused by a different rule must not be merged into boundary rule."""
    sig_boundary_rule = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="OPERATOR_CHANGED",
        analysis_path="columns[risk_class]",
        source_expression="amount > 500",
        target_expression="amount >= 500",
        payload={"column": "risk_class"},
    )
    sig_unrelated_row = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="columns[total_amount]",
        source_expression="100.0",
        target_expression="200.0",
        payload={"column": "total_amount", "mismatch_count": 50},
    )

    consolidator = EvidenceConsolidator()
    report = consolidator.consolidate(
        "val-test-d", [sig_boundary_rule, sig_unrelated_row], total_output_rows=1000
    )

    assert len(report) == 2
    boundary_disc = [d for d in report if d.category == DiscrepancyCategory.BOUNDARY_CONDITION][0]
    assert boundary_disc.affected_output_columns == ["risk_class"]
    assert boundary_disc.affected_row_count in (0, None)  # Row mismatch was on total_amount, not merged!


def test_regression_e_structural_rule_diff_unrelated_row_mismatch_separate():
    """E. Structural rule difference with unrelated row mismatch must remain separate."""
    sig_struct = RawDiscrepancySignal(
        source_validator="BusinessRuleValidator",
        signal_type="CASE_RULE_CHANGED",
        analysis_path="columns[tier]",
        source_expression="score > 700 THEN 'GOLD'",
        target_expression="score > 750 THEN 'GOLD'",
        payload={"column": "tier"},
    )
    sig_unrelated_row = RawDiscrepancySignal(
        source_validator="RowValidator",
        signal_type="VALUE_MISMATCH",
        analysis_path="columns[fee]",
        source_expression="10",
        target_expression="15",
        payload={"column": "fee", "mismatch_count": 12},
    )

    consolidator = EvidenceConsolidator()
    report = consolidator.consolidate(
        "val-test-e", [sig_struct, sig_unrelated_row], total_output_rows=500
    )

    assert len(report) == 2
    disc_ids = [d.discrepancy_id for d in report]
    assert len(disc_ids) == 2
