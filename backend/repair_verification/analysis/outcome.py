"""OutcomeCalculator — computes row reduction metrics and evidence payloads for Phase 8."""

from __future__ import annotations

from backend.diagnosis.models import DiscrepancyReport
from backend.repair_verification.analysis.discrepancy_diff import DiscrepancyDiffAnalyzer
from backend.repair_verification.models import (
    RepairOutcome,
    VerificationEvidenceItem,
)


class OutcomeCalculator:
    """Calculates quantitative outcome metrics and builds structured evidence lists."""

    @classmethod
    def calculate_reduction_metrics(cls, rows_before: int | None, rows_after: int | None) -> tuple[int | None, float]:
        """Calculate reduction count and reduction percentage with zero-division safety."""
        if rows_before is None or rows_after is None:
            return 0, 0.0
        if rows_before <= 0:
            return 0, 0.0

        reduction_count = max(0, rows_before - rows_after)
        reduction_percentage = round((reduction_count / rows_before) * 100.0, 2)
        return reduction_count, reduction_percentage

    @classmethod
    def build_verification_evidence(
        cls,
        val_id_before: str,
        val_id_after: str | None,
        rows_before: int,
        rows_after: int,
        target_signature_before: str,
        target_signature_after: str | None,
        resolved_ids: list[str],
        new_ids: list[str],
    ) -> list[VerificationEvidenceItem]:
        """Build stable evidence items (EV-001 to EV-007)."""
        ev_items: list[VerificationEvidenceItem] = []

        # EV-001: BEFORE validation ID
        ev_items.append(
            VerificationEvidenceItem(
                evidence_id="EV-001",
                evidence_type="BEFORE_VALIDATION_REF",
                description="Original BEFORE validation run ID reference",
                details={"validation_id_before": val_id_before},
            )
        )

        # EV-002: AFTER validation ID
        if val_id_after:
            ev_items.append(
                VerificationEvidenceItem(
                    evidence_id="EV-002",
                    evidence_type="AFTER_VALIDATION_REF",
                    description="Re-validation AFTER run ID reference",
                    details={"validation_id_after": val_id_after},
                )
            )

        # EV-003: Affected rows before
        ev_items.append(
            VerificationEvidenceItem(
                evidence_id="EV-003",
                evidence_type="AFFECTED_ROWS_BEFORE",
                description="Number of affected result rows before repair",
                details={"affected_rows_before": rows_before},
            )
        )

        # EV-004: Affected rows after
        ev_items.append(
            VerificationEvidenceItem(
                evidence_id="EV-004",
                evidence_type="AFFECTED_ROWS_AFTER",
                description="Number of affected result rows after repair",
                details={"affected_rows_after": rows_after},
            )
        )

        # EV-005: Target discrepancy signature before
        ev_items.append(
            VerificationEvidenceItem(
                evidence_id="EV-005",
                evidence_type="TARGET_SIGNATURE_BEFORE",
                description="Original target discrepancy semantic signature",
                details={"signature_before": target_signature_before},
            )
        )

        # EV-006: Target discrepancy absent/resolved after
        if target_signature_after is None:
            ev_items.append(
                VerificationEvidenceItem(
                    evidence_id="EV-006",
                    evidence_type="TARGET_DISCREPANCY_RESOLVED",
                    description="Targeted discrepancy absent in AFTER re-validation report",
                    details={"resolved_discrepancy_ids": resolved_ids},
                )
            )
        else:
            ev_items.append(
                VerificationEvidenceItem(
                    evidence_id="EV-006",
                    evidence_type="TARGET_DISCREPANCY_PERSISTS",
                    description="Targeted discrepancy persists in AFTER re-validation report",
                    details={"signature_after": target_signature_after},
                )
            )

        # EV-007: New discrepancies introduced
        if new_ids:
            ev_items.append(
                VerificationEvidenceItem(
                    evidence_id="EV-007",
                    evidence_type="NEW_DISCREPANCIES_INTRODUCED",
                    description="Newly introduced semantic discrepancies detected in AFTER run",
                    details={"new_discrepancy_ids": new_ids},
                )
            )

        return ev_items

    @classmethod
    def calculate_repair_outcome(
        cls,
        before_report: DiscrepancyReport,
        after_report: DiscrepancyReport | None,
        target_discrepancy_id: str,
        val_id_before: str,
        val_id_after: str | None,
    ) -> tuple[RepairOutcome, list[str], list[str], list[str], list[VerificationEvidenceItem]]:
        """Calculate complete RepairOutcome and evidence payload."""
        target_outcome, resolved_ids, remaining_ids, new_ids = (
            DiscrepancyDiffAnalyzer.categorize_before_and_after_discrepancies(
                before_report=before_report,
                after_report=after_report,
                target_discrepancy_id=target_discrepancy_id,
            )
        )

        rows_before = target_outcome.affected_rows_before
        rows_after = target_outcome.affected_rows_after
        red_count, red_pct = cls.calculate_reduction_metrics(rows_before, rows_after)

        before_recs = before_report.discrepancies if before_report else []
        target_before = next((r for r in before_recs if r.discrepancy_id == target_discrepancy_id), None)
        target_sig_before = (
            DiscrepancyDiffAnalyzer.compute_semantic_signature(target_before)
            if target_before
            else "UNKNOWN"
        )
        target_sig_after = (
            target_outcome.matching_after_discrepancy_ids[0]
            if target_outcome.matching_after_discrepancy_ids
            else None
        )

        evidence = cls.build_verification_evidence(
            val_id_before=val_id_before,
            val_id_after=val_id_after,
            rows_before=rows_before,
            rows_after=rows_after,
            target_signature_before=target_sig_before,
            target_signature_after=target_sig_after,
            resolved_ids=resolved_ids,
            new_ids=new_ids,
        )

        repair_outcome = RepairOutcome(
            discrepancy_id_before=target_discrepancy_id,
            status=target_outcome.status,
            affected_rows_before=rows_before,
            affected_rows_after=rows_after,
            reduction_count=red_count,
            reduction_percentage=red_pct,
            matching_after_discrepancy_ids=target_outcome.matching_after_discrepancy_ids,
            new_discrepancy_ids=new_ids,
            evidence=evidence,
            summary=target_outcome.summary,
        )

        return repair_outcome, resolved_ids, remaining_ids, new_ids, evidence
