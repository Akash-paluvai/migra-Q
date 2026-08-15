"""VerificationStatusDeterminer — deterministic decision engine for Phase 8 repair verification."""

from __future__ import annotations

from backend.repair_verification.models import (
    DiscrepancyOutcomeStatus,
    RepairOutcome,
    VerificationStatus,
)


class VerificationStatusDeterminer:
    """Evaluates comparative evidence against strict rule-based decision matrix to determine VerificationStatus."""

    @classmethod
    def determine_status(
        cls,
        candidate_valid: bool,
        rejection_reason: str | None,
        execution_succeeded: bool,
        target_outcome: RepairOutcome,
        new_discrepancies: list[str],
        contract_preserved: bool = True,
        dataset_unchanged: bool = True,
        config_unchanged: bool = True,
        immutability_error: str | None = None,
    ) -> tuple[VerificationStatus, str]:
        """Deterministically compute VerificationStatus based on evidence metrics.

        Returns (VerificationStatus, summary_explanation).
        """
        # Rule 1: Candidate rejected pre-execution
        if not candidate_valid:
            reason = rejection_reason or "CANDIDATE_REJECTED"
            return (
                VerificationStatus.CANDIDATE_REJECTED,
                f"Candidate repair rejected before execution: {reason}.",
            )

        # Rule 2: Execution failure
        if not execution_succeeded:
            return (
                VerificationStatus.EXECUTION_FAILED,
                "Repaired SQL execution failed in DuckDB sandbox environment.",
            )

        # Rule 3: Immutability violation
        if not dataset_unchanged or immutability_error == "DATASET_CHANGED":
            return (
                VerificationStatus.FAILED_VERIFICATION,
                "FAILED_VERIFICATION: Dataset hash changed between BEFORE and AFTER runs.",
            )

        if not config_unchanged or immutability_error == "VALIDATION_CONFIGURATION_CHANGED":
            return (
                VerificationStatus.FAILED_VERIFICATION,
                "FAILED_VERIFICATION: Validation configuration changed between BEFORE and AFTER runs.",
            )

        # Rule 4: Output contract violation
        if not contract_preserved:
            return (
                VerificationStatus.FAILED_VERIFICATION,
                "FAILED_VERIFICATION: Repaired SQL broke target output contract (aliases/columns mismatched).",
            )

        # Rule 5: New discrepancies introduced (Regressions take priority over resolution!)
        if len(new_discrepancies) > 0:
            return (
                VerificationStatus.NEW_DISCREPANCIES,
                f"NEW_DISCREPANCIES: Repair introduced {len(new_discrepancies)} new semantic discrepancy regressions ({', '.join(new_discrepancies)}).",
            )

        # Rule 6: Targeted discrepancy resolved -> VERIFIED
        if target_outcome.status == DiscrepancyOutcomeStatus.RESOLVED:
            if target_outcome.affected_rows_before == 0:
                return (
                    VerificationStatus.FAILED_VERIFICATION,
                    (
                        f"FAILED_VERIFICATION: Targeted discrepancy '{target_outcome.discrepancy_id_before}' had "
                        f"0 affected rows before repair. 0 -> 0 cannot yield VERIFIED status for behavioral discrepancy."
                    ),
                )
            return (
                VerificationStatus.VERIFIED,
                (
                    f"VERIFIED: Targeted discrepancy '{target_outcome.discrepancy_id_before}' resolved "
                    f"({target_outcome.affected_rows_before} → {target_outcome.affected_rows_after} affected rows, "
                    f"100.0% reduction, 0 new discrepancies)."
                ),
            )

        # Rule 7: Targeted discrepancy partially resolved
        if target_outcome.status == DiscrepancyOutcomeStatus.PERSISTS and target_outcome.reduction_percentage > 0:
            return (
                VerificationStatus.PARTIALLY_RESOLVED,
                (
                    f"PARTIALLY_RESOLVED: Targeted discrepancy '{target_outcome.discrepancy_id_before}' improved "
                    f"({target_outcome.affected_rows_before} → {target_outcome.affected_rows_after} affected rows, "
                    f"{target_outcome.reduction_percentage}% reduction)."
                ),
            )

        # Rule 8: Targeted discrepancy persists completely -> FAILED_VERIFICATION
        return (
            VerificationStatus.FAILED_VERIFICATION,
            (
                f"FAILED_VERIFICATION: Targeted discrepancy '{target_outcome.discrepancy_id_before}' persists "
                f"({target_outcome.affected_rows_after} affected rows remaining, 0% reduction)."
            ),
        )
