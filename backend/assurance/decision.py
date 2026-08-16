"""Decision engine — single deterministic function determines VERIFIED status.

The score describes evidence. The gates determine the decision.
No LLM involvement. No score-based thresholds.
"""

from __future__ import annotations

from backend.assurance.models import (
    GateOutcome,
    HardGateEvaluation,
    MigrationFinalStatus,
    VerificationPath,
)


def determine_verified(
    *,
    translation_valid: bool,
    source_execution_succeeded: bool,
    target_execution_succeeded: bool,
    schema_valid: bool,
    remaining_discrepancy_count: int,
    new_discrepancy_count: int,
    repair_verification_passed: bool | None,  # None if no repair
    dataset_unchanged: bool | None,           # None if no repair
    validation_config_unchanged: bool | None, # None if no repair
    audit_lineage_complete: bool,
) -> bool:
    """Single deterministic function that computes whether a migration is VERIFIED.

    VERIFIED iff:
      - translation valid
      - AND source execution successful
      - AND target execution successful
      - AND schema valid
      - AND zero unresolved discrepancies
      - AND no new discrepancies
      - AND repair verification passed (if repair occurred)
      - AND dataset unchanged (if repair occurred)
      - AND validation configuration unchanged (if repair occurred)
      - AND audit lineage complete

    Returns:
        True if and only if all conditions are satisfied.
    """
    if not translation_valid:
        return False
    if not source_execution_succeeded:
        return False
    if not target_execution_succeeded:
        return False
    if not schema_valid:
        return False
    if remaining_discrepancy_count != 0:
        return False
    if new_discrepancy_count != 0:
        return False
    if repair_verification_passed is not None and not repair_verification_passed:
        return False
    if dataset_unchanged is not None and not dataset_unchanged:
        return False
    if validation_config_unchanged is not None and not validation_config_unchanged:
        return False
    if not audit_lineage_complete:
        return False
    return True


class DecisionEngine:
    """Determines migration final status from hard gate evaluation.

    Decision rules:
      - VERIFIED: All gates passed (PASS or NOT_APPLICABLE).
      - BLOCKED: At least one gate failed, migration has a structural issue.
      - FAILED: At least one gate failed, migration cannot proceed.
      - IN_PROGRESS: Evaluation not complete.
      - ERROR: System error prevented evaluation.
    """

    def determine_final_status(
        self,
        gate_evaluation: HardGateEvaluation,
        verification_path: VerificationPath,
    ) -> tuple[MigrationFinalStatus, str]:
        """Determine the final migration status from gate evaluation results.

        Args:
            gate_evaluation: Aggregated hard gate evaluation results.
            verification_path: The path taken (DIRECT_PASS or REPAIRED_PASS).

        Returns:
            Tuple of (MigrationFinalStatus, decision_reason).
        """
        if gate_evaluation.all_passed:
            path_desc = (
                "direct validation" if verification_path == VerificationPath.DIRECT_PASS
                else "deterministic re-validation after repair"
            )
            applicable_count = gate_evaluation.passed_count + gate_evaluation.not_applicable_count
            return (
                MigrationFinalStatus.VERIFIED,
                f"Verified by {path_desc}. "
                f"All {applicable_count} hard gates passed "
                f"({gate_evaluation.passed_count} PASS, "
                f"{gate_evaluation.not_applicable_count} NOT_APPLICABLE).",
            )

        # At least one gate failed — build reason from failed gates
        failed_gates = [
            g for g in gate_evaluation.gates if g.outcome == GateOutcome.FAIL
        ]
        failed_descriptions = [
            f"{g.gate_id} ({g.gate_name}): {g.reason}" for g in failed_gates
        ]

        # Determine BLOCKED vs FAILED based on failure type
        # Technical prerequisite failures (translation, execution, lineage) → FAILED
        # Semantic evaluation failures (discrepancies, repair incomplete) → BLOCKED
        technical_gate_ids = {"GATE-001", "GATE-002", "GATE-003", "GATE-010"}
        has_technical_failure = any(
            g.gate_id in technical_gate_ids for g in failed_gates
        )

        if has_technical_failure:
            return (
                MigrationFinalStatus.FAILED,
                "Migration assurance evaluation could not be completed due to technical prerequisite failure. "
                f"Failed gates: {'; '.join(failed_descriptions)}",
            )

        return (
            MigrationFinalStatus.BLOCKED,
            "Migration contains unresolved semantic issues. "
            f"Failed gates: {'; '.join(failed_descriptions)}",
        )
