"""Tests for Phase 9 hard gate evaluator."""

import pytest

from backend.assurance.gates import HardGateEvaluator
from backend.assurance.models import GateOutcome


@pytest.fixture
def evaluator():
    return HardGateEvaluator()


def _all_pass_kwargs(**overrides):
    """Return kwargs that make all 11 gates pass."""
    defaults = dict(
        source_execution_succeeded=True,
        translation_syntactically_valid=True,
        target_execution_succeeded=True,
        schema_valid=True,
        has_unresolved_critical=False,
        remaining_discrepancy_count=0,
        repair_attempted=True,
        new_discrepancy_count_after_repair=0,
        repair_verification_status="VERIFIED",
        dataset_hash_unchanged=True,
        validation_config_hash_unchanged=True,
        audit_lineage_complete=True,
    )
    defaults.update(overrides)
    return defaults


class TestAllGatesPass:
    def test_all_11_gates_pass(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs())
        assert result.all_passed is True
        assert result.total_gates == 11
        assert result.failed_count == 0

    def test_all_gates_pass_direct_path(self, evaluator):
        """DIRECT_PASS path — repair gates are NOT_APPLICABLE."""
        result = evaluator.evaluate(**_all_pass_kwargs(repair_attempted=False))
        assert result.all_passed is True
        # GATE-006, 007, 008, 009 should be NOT_APPLICABLE
        assert result.not_applicable_count == 4


class TestIndividualGateFailures:
    def test_gate_001_source_execution_failed(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(source_execution_succeeded=False))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-001")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_002_translation_invalid(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(translation_syntactically_valid=False))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-002")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_003_target_execution_failed(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(target_execution_succeeded=False))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-003")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_004_schema_mismatch(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(schema_valid=False))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-004")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_005_critical_discrepancy(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(has_unresolved_critical=True))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-005")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_006_new_discrepancies_after_repair(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(new_discrepancy_count_after_repair=2))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-006")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_007_repair_not_verified(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(repair_verification_status="FAILED_VERIFICATION"))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-007")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_008_dataset_hash_changed(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(dataset_hash_unchanged=False))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-008")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_009_config_hash_changed(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(validation_config_hash_unchanged=False))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-009")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_010_lineage_incomplete(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(audit_lineage_complete=False))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-010")
        assert gate.outcome == GateOutcome.FAIL

    def test_gate_011_unresolved_discrepancies(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(remaining_discrepancy_count=1))
        assert result.all_passed is False
        gate = next(g for g in result.gates if g.gate_id == "GATE-011")
        assert gate.outcome == GateOutcome.FAIL


class TestGateNotApplicableSemantics:
    def test_repair_gates_not_applicable_when_no_repair(self, evaluator):
        result = evaluator.evaluate(**_all_pass_kwargs(repair_attempted=False))
        repair_gate_ids = {"GATE-006", "GATE-007", "GATE-008", "GATE-009"}
        for gate in result.gates:
            if gate.gate_id in repair_gate_ids:
                assert gate.outcome == GateOutcome.NOT_APPLICABLE, f"{gate.gate_id} should be NOT_APPLICABLE"

    def test_not_applicable_does_not_block(self, evaluator):
        """NOT_APPLICABLE gates should not cause all_passed to be False."""
        result = evaluator.evaluate(**_all_pass_kwargs(repair_attempted=False))
        assert result.all_passed is True


class TestGateOverridesScore:
    def test_single_fail_blocks_even_with_all_others_passing(self, evaluator):
        """Score = 100 but GATE-011 fails → not verified."""
        result = evaluator.evaluate(**_all_pass_kwargs(remaining_discrepancy_count=1))
        assert result.all_passed is False
        assert result.failed_count == 1

    def test_score_99_but_gate_fails(self, evaluator):
        """Simulates: Score=99, Hard Gates=10/11, Remaining=1 → BLOCKED."""
        result = evaluator.evaluate(**_all_pass_kwargs(remaining_discrepancy_count=1))
        assert result.all_passed is False
        gate_011 = next(g for g in result.gates if g.gate_id == "GATE-011")
        assert gate_011.outcome == GateOutcome.FAIL
