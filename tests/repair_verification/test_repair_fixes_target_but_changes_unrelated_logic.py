"""Mandatory regression test: Repair fixing targeted discrepancy but introducing unrelated regression yields NEW_DISCREPANCIES."""

from backend.diagnosis.models import DiscrepancyCategory, DiscrepancyRecord, DiscrepancyReport
from backend.repair_verification.analysis.discrepancy_diff import DiscrepancyDiffAnalyzer
from backend.repair_verification.models import (
    DiscrepancyOutcomeStatus,
    VerificationStatus,
)
from backend.repair_verification.status import VerificationStatusDeterminer


def test_repair_fixes_target_but_changes_unrelated_logic():
    """Verify that if a repair resolves D-001 (BOUNDARY_CONDITION) but introduces D-002 (AGGREGATION_SEMANTICS in group_by),

    the final verification status is strictly NEW_DISCREPANCIES, NOT VERIFIED.
    """
    d1_before = DiscrepancyRecord(
        discrepancy_id="D-001",
        validation_id="val-1",
        category=DiscrepancyCategory.BOUNDARY_CONDITION,
        severity="HIGH",  # type: ignore[arg-type]
        classification_confidence=1.0,
        classification_method="DETERMINISTIC_RULE",  # type: ignore[arg-type]
        classification_reason="Boundary shift",
        source_expression="t.amount > 500",
        target_expression="t.amount >= 500",
        affected_output_columns=["risk_class"],
        affected_row_count=10512,
        total_output_rows=10512,
        analysis_path="where_clause",
        created_at="2026-08-15T12:00:00Z",
    )

    d2_after = DiscrepancyRecord(
        discrepancy_id="D-002",
        validation_id="val-2",
        category=DiscrepancyCategory.AGGREGATION_SEMANTICS,
        severity="HIGH",  # type: ignore[arg-type]
        classification_confidence=1.0,
        classification_method="DETERMINISTIC_RULE",  # type: ignore[arg-type]
        classification_reason="Group by column missing",
        source_expression="GROUP BY c.customer_id, c.customer_segment",
        target_expression="GROUP BY c.customer_id",
        affected_output_columns=["total_amount"],
        affected_row_count=10512,
        total_output_rows=10512,
        analysis_path="group_by_clause",
        created_at="2026-08-15T12:00:00Z",
    )

    before_report = DiscrepancyReport(diagnosis_id="diag-1", validation_id="val-1", discrepancies=[d1_before])
    after_report = DiscrepancyReport(diagnosis_id="diag-2", validation_id="val-2", discrepancies=[d2_after])

    target_outcome, resolved, remaining, new_ids = (
        DiscrepancyDiffAnalyzer.categorize_before_and_after_discrepancies(
            before_report=before_report,
            after_report=after_report,
            target_discrepancy_id="D-001",
        )
    )

    # 1. Target D-001 itself is resolved
    assert target_outcome.status == DiscrepancyOutcomeStatus.RESOLVED
    assert "D-001" in resolved

    # 2. D-002 is correctly detected as a NEW discrepancy regression
    assert "D-002" in new_ids

    # 3. VerificationStatusDeterminer MUST return NEW_DISCREPANCIES, NOT VERIFIED
    status, summary = VerificationStatusDeterminer.determine_status(
        candidate_valid=True,
        rejection_reason=None,
        execution_succeeded=True,
        target_outcome=target_outcome,
        new_discrepancies=new_ids,
        contract_preserved=True,
        dataset_unchanged=True,
        config_unchanged=True,
    )

    assert status == VerificationStatus.NEW_DISCREPANCIES
    assert status != VerificationStatus.VERIFIED
    assert "NEW_DISCREPANCIES" in summary
    assert "D-002" in summary
