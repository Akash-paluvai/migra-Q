"""Unit tests for DiscrepancyDiffAnalyzer hierarchical resolution logic and diffing."""

from backend.diagnosis.models import DiscrepancyCategory, DiscrepancyRecord, DiscrepancyReport
from backend.repair_verification.analysis.discrepancy_diff import DiscrepancyDiffAnalyzer
from backend.repair_verification.models import DiscrepancyOutcomeStatus


def _build_record(
    disc_id: str,
    category: DiscrepancyCategory,
    affected_rows: int = 100,
    analysis_path: str = "where_clause",
    source_expr: str = "t.amount > 500",
    target_expr: str = "t.amount >= 500",
) -> DiscrepancyRecord:
    return DiscrepancyRecord(
        discrepancy_id=disc_id,
        validation_id="val-001",
        category=category,
        severity="HIGH",  # type: ignore[arg-type]
        classification_confidence=1.0,
        classification_method="DETERMINISTIC_RULE",  # type: ignore[arg-type]
        classification_reason="Testing",
        source_expression=source_expr,
        target_expression=target_expr,
        affected_output_columns=["risk_class"],
        affected_row_count=affected_rows,
        total_output_rows=1000,
        analysis_path=analysis_path,
        created_at="2026-08-15T12:00:00Z",
    )


def test_compute_semantic_signature():
    rec = _build_record("D-001", DiscrepancyCategory.BOUNDARY_CONDITION)
    sig = DiscrepancyDiffAnalyzer.compute_semantic_signature(rec)
    assert "BOUNDARY_CONDITION" in sig
    assert "where_clause" in sig
    assert "500" in sig


def test_hierarchical_step_1_exact_signature_persists():
    r_before = _build_record("D-001", DiscrepancyCategory.BOUNDARY_CONDITION, affected_rows=10512)
    _before_report = DiscrepancyReport(diagnosis_id="diag-1", validation_id="val-1", discrepancies=[r_before])
    after_report = DiscrepancyReport(diagnosis_id="diag-2", validation_id="val-2", discrepancies=[r_before])

    outcome = DiscrepancyDiffAnalyzer.analyze_targeted_discrepancy(r_before, after_report)
    assert outcome.status == DiscrepancyOutcomeStatus.PERSISTS
    assert outcome.affected_rows_after == 10512
    assert outcome.reduction_percentage == 0.0


def test_hierarchical_step_2_region_match_persists():
    r_before = _build_record("D-001", DiscrepancyCategory.BOUNDARY_CONDITION, affected_rows=10512)
    r_after = _build_record("D-002", DiscrepancyCategory.BOUNDARY_CONDITION, affected_rows=5000)
    _before_report = DiscrepancyReport(diagnosis_id="diag-1", validation_id="val-1", discrepancies=[r_before])
    after_report = DiscrepancyReport(diagnosis_id="diag-2", validation_id="val-2", discrepancies=[r_after])

    outcome = DiscrepancyDiffAnalyzer.analyze_targeted_discrepancy(r_before, after_report)
    assert outcome.status == DiscrepancyOutcomeStatus.PERSISTS
    assert outcome.affected_rows_after == 5000
    assert outcome.reduction_count == 5512
    assert outcome.reduction_percentage == 52.44


def test_hierarchical_step_3_region_replacement_changed():
    r_before = _build_record("D-001", DiscrepancyCategory.BOUNDARY_CONDITION, affected_rows=10512)
    r_after = _build_record("D-002", DiscrepancyCategory.FILTER_LOGIC, affected_rows=10512)
    _before_report = DiscrepancyReport(diagnosis_id="diag-1", validation_id="val-1", discrepancies=[r_before])
    after_report = DiscrepancyReport(diagnosis_id="diag-2", validation_id="val-2", discrepancies=[r_after])

    outcome = DiscrepancyDiffAnalyzer.analyze_targeted_discrepancy(r_before, after_report)
    assert outcome.status == DiscrepancyOutcomeStatus.CHANGED
    assert "D-002" in outcome.new_discrepancy_ids


def test_hierarchical_step_4_absent_in_after_resolved():
    r_before = _build_record("D-001", DiscrepancyCategory.BOUNDARY_CONDITION, affected_rows=10512)
    _before_report = DiscrepancyReport(diagnosis_id="diag-1", validation_id="val-1", discrepancies=[r_before])
    after_report = DiscrepancyReport(diagnosis_id="diag-2", validation_id="val-2", discrepancies=[])

    outcome = DiscrepancyDiffAnalyzer.analyze_targeted_discrepancy(r_before, after_report)
    assert outcome.status == DiscrepancyOutcomeStatus.RESOLVED
    assert outcome.affected_rows_after == 0
    assert outcome.reduction_percentage == 100.0


def test_before_existing_vs_after_new_diffing():
    d1 = _build_record("D-001", DiscrepancyCategory.BOUNDARY_CONDITION)
    d2 = _build_record("D-002", DiscrepancyCategory.NULL_SEMANTICS, analysis_path="select_projections")
    d3 = _build_record("D-003", DiscrepancyCategory.AGGREGATION_SEMANTICS, analysis_path="group_by")

    before_report = DiscrepancyReport(diagnosis_id="diag-1", validation_id="val-1", discrepancies=[d1, d2])
    after_report = DiscrepancyReport(diagnosis_id="diag-2", validation_id="val-2", discrepancies=[d2, d3])

    target_outcome, resolved, remaining, new_ids = (
        DiscrepancyDiffAnalyzer.categorize_before_and_after_discrepancies(
            before_report=before_report,
            after_report=after_report,
            target_discrepancy_id="D-001",
        )
    )

    assert target_outcome.status == DiscrepancyOutcomeStatus.RESOLVED
    assert "D-001" in resolved
    assert "D-002" in remaining
    assert "D-003" in new_ids  # D-003 is newly introduced regression!
