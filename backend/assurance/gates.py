"""Hard gate evaluator — 11 mandatory gates that determine the migration decision.

The score describes evidence. The gates determine the decision.
A single FAIL gate blocks VERIFIED status regardless of assurance score.
"""

from __future__ import annotations

from backend.assurance.models import (
    GateOutcome,
    HardGateEvaluation,
    HardGateResult,
)


class HardGateEvaluator:
    """Evaluates 11 mandatory hard gates against Phase 1–8 artifacts.

    Gate outcomes:
      - PASS: condition satisfied
      - FAIL: condition NOT satisfied
      - NOT_APPLICABLE: gate does not apply to this migration path

    all_passed is True iff every gate has outcome PASS or NOT_APPLICABLE.
    """

    def evaluate(
        self,
        *,
        source_execution_succeeded: bool,
        translation_syntactically_valid: bool,
        target_execution_succeeded: bool,
        schema_valid: bool,
        has_unresolved_critical: bool,
        remaining_discrepancy_count: int,
        repair_attempted: bool,
        new_discrepancy_count_after_repair: int | None = None,
        repair_verification_status: str | None = None,
        dataset_hash_unchanged: bool | None = None,
        validation_config_hash_unchanged: bool | None = None,
        audit_lineage_complete: bool = False,
    ) -> HardGateEvaluation:
        """Evaluate all 11 hard gates and return aggregated results.

        Args:
            source_execution_succeeded: Phase 3 source execution status == SUCCESS.
            translation_syntactically_valid: Phase 6 candidate_validation_status == VALID_SYNTAX.
            target_execution_succeeded: Phase 3 target execution status == SUCCESS.
            schema_valid: Phase 4 SchemaValidator status != FAIL.
            has_unresolved_critical: Any remaining discrepancy with CRITICAL severity.
            remaining_discrepancy_count: Number of remaining unresolved discrepancies.
            repair_attempted: Whether a repair was attempted (Phase 7/8 path).
            new_discrepancy_count_after_repair: Phase 8 new_discrepancy_count (None if no repair).
            repair_verification_status: Phase 8 verification status string (None if no repair).
            dataset_hash_unchanged: Phase 8 dataset_hash_before == dataset_hash_after (None if no repair).
            validation_config_hash_unchanged: Phase 8 config_hash_before == config_hash_after (None if no repair).
            audit_lineage_complete: Whether all required artifact IDs are present.

        Returns:
            HardGateEvaluation with all 11 gate results.
        """
        gates: list[HardGateResult] = []

        # GATE-001: Source execution succeeded
        gates.append(HardGateResult(
            gate_id="GATE-001",
            gate_name="Source execution succeeded",
            outcome=GateOutcome.PASS if source_execution_succeeded else GateOutcome.FAIL,
            reason="Source execution completed successfully." if source_execution_succeeded
            else "Source execution did not succeed.",
        ))

        # GATE-002: Target translation syntactically valid
        gates.append(HardGateResult(
            gate_id="GATE-002",
            gate_name="Target translation syntactically valid",
            outcome=GateOutcome.PASS if translation_syntactically_valid else GateOutcome.FAIL,
            reason="Target SQL passed syntactic validation." if translation_syntactically_valid
            else "Target SQL failed syntactic validation.",
        ))

        # GATE-003: Target execution succeeded
        gates.append(HardGateResult(
            gate_id="GATE-003",
            gate_name="Target execution succeeded",
            outcome=GateOutcome.PASS if target_execution_succeeded else GateOutcome.FAIL,
            reason="Target execution completed successfully." if target_execution_succeeded
            else "Target execution did not succeed.",
        ))

        # GATE-004: No schema mismatch
        gates.append(HardGateResult(
            gate_id="GATE-004",
            gate_name="No schema mismatch",
            outcome=GateOutcome.PASS if schema_valid else GateOutcome.FAIL,
            reason="Schema validation passed." if schema_valid
            else "Schema validation failed.",
        ))

        # GATE-005: No unresolved CRITICAL discrepancy
        gates.append(HardGateResult(
            gate_id="GATE-005",
            gate_name="No unresolved CRITICAL discrepancy",
            outcome=GateOutcome.PASS if not has_unresolved_critical else GateOutcome.FAIL,
            reason="No CRITICAL severity discrepancies remain." if not has_unresolved_critical
            else "Unresolved CRITICAL severity discrepancy detected.",
        ))

        # GATE-006: No new discrepancy after repair
        if repair_attempted:
            no_new = (new_discrepancy_count_after_repair or 0) == 0
            gates.append(HardGateResult(
                gate_id="GATE-006",
                gate_name="No new discrepancy after repair",
                outcome=GateOutcome.PASS if no_new else GateOutcome.FAIL,
                reason="No new discrepancies introduced by repair." if no_new
                else f"Repair introduced {new_discrepancy_count_after_repair} new discrepancies.",
            ))
        else:
            gates.append(HardGateResult(
                gate_id="GATE-006",
                gate_name="No new discrepancy after repair",
                outcome=GateOutcome.NOT_APPLICABLE,
                reason="No repair was attempted.",
            ))

        # GATE-007: Repair verification VERIFIED
        if repair_attempted:
            verified = repair_verification_status == "VERIFIED"
            gates.append(HardGateResult(
                gate_id="GATE-007",
                gate_name="Repair verification VERIFIED",
                outcome=GateOutcome.PASS if verified else GateOutcome.FAIL,
                reason="Repair verification completed with VERIFIED status." if verified
                else f"Repair verification status: {repair_verification_status}.",
            ))
        else:
            gates.append(HardGateResult(
                gate_id="GATE-007",
                gate_name="Repair verification VERIFIED",
                outcome=GateOutcome.NOT_APPLICABLE,
                reason="No repair was attempted.",
            ))

        # GATE-008: Dataset hash unchanged
        if repair_attempted:
            unchanged = dataset_hash_unchanged is True
            gates.append(HardGateResult(
                gate_id="GATE-008",
                gate_name="Dataset hash unchanged",
                outcome=GateOutcome.PASS if unchanged else GateOutcome.FAIL,
                reason="Dataset hash unchanged between before and after." if unchanged
                else "Dataset hash changed during repair verification.",
            ))
        else:
            gates.append(HardGateResult(
                gate_id="GATE-008",
                gate_name="Dataset hash unchanged",
                outcome=GateOutcome.NOT_APPLICABLE,
                reason="No repair was attempted.",
            ))

        # GATE-009: Validation config unchanged
        if repair_attempted:
            config_ok = validation_config_hash_unchanged is True
            gates.append(HardGateResult(
                gate_id="GATE-009",
                gate_name="Validation config unchanged",
                outcome=GateOutcome.PASS if config_ok else GateOutcome.FAIL,
                reason="Validation configuration hash unchanged." if config_ok
                else "Validation configuration changed during repair verification.",
            ))
        else:
            gates.append(HardGateResult(
                gate_id="GATE-009",
                gate_name="Validation config unchanged",
                outcome=GateOutcome.NOT_APPLICABLE,
                reason="No repair was attempted.",
            ))

        # GATE-010: Audit lineage complete
        gates.append(HardGateResult(
            gate_id="GATE-010",
            gate_name="Audit lineage complete",
            outcome=GateOutcome.PASS if audit_lineage_complete else GateOutcome.FAIL,
            reason="All required artifact IDs present in audit lineage." if audit_lineage_complete
            else "Audit lineage is incomplete — missing required artifact IDs.",
        ))

        # GATE-011: No unresolved semantic discrepancies
        no_unresolved = remaining_discrepancy_count == 0
        gates.append(HardGateResult(
            gate_id="GATE-011",
            gate_name="No unresolved semantic discrepancies",
            outcome=GateOutcome.PASS if no_unresolved else GateOutcome.FAIL,
            reason="Zero unresolved semantic discrepancies." if no_unresolved
            else f"{remaining_discrepancy_count} unresolved semantic discrepancies remain.",
        ))

        # Aggregate
        passed = sum(1 for g in gates if g.outcome == GateOutcome.PASS)
        failed = sum(1 for g in gates if g.outcome == GateOutcome.FAIL)
        na = sum(1 for g in gates if g.outcome == GateOutcome.NOT_APPLICABLE)

        return HardGateEvaluation(
            gates=gates,
            all_passed=(failed == 0),
            total_gates=len(gates),
            passed_count=passed,
            failed_count=failed,
            not_applicable_count=na,
        )
