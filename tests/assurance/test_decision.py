"""Tests for Phase 9 decision engine."""

import pytest

from backend.assurance.decision import DecisionEngine, determine_verified
from backend.assurance.models import (
    GateOutcome,
    HardGateEvaluation,
    HardGateResult,
    MigrationFinalStatus,
    VerificationPath,
)


class TestDetermineVerified:
    def test_all_conditions_met(self):
        assert determine_verified(
            translation_valid=True,
            source_execution_succeeded=True,
            target_execution_succeeded=True,
            schema_valid=True,
            remaining_discrepancy_count=0,
            new_discrepancy_count=0,
            repair_verification_passed=True,
            dataset_unchanged=True,
            validation_config_unchanged=True,
            audit_lineage_complete=True,
        ) is True

    def test_no_repair_all_met(self):
        assert determine_verified(
            translation_valid=True,
            source_execution_succeeded=True,
            target_execution_succeeded=True,
            schema_valid=True,
            remaining_discrepancy_count=0,
            new_discrepancy_count=0,
            repair_verification_passed=None,
            dataset_unchanged=None,
            validation_config_unchanged=None,
            audit_lineage_complete=True,
        ) is True

    def test_translation_invalid(self):
        assert determine_verified(
            translation_valid=False,
            source_execution_succeeded=True,
            target_execution_succeeded=True,
            schema_valid=True,
            remaining_discrepancy_count=0,
            new_discrepancy_count=0,
            repair_verification_passed=None,
            dataset_unchanged=None,
            validation_config_unchanged=None,
            audit_lineage_complete=True,
        ) is False

    def test_unresolved_discrepancies(self):
        assert determine_verified(
            translation_valid=True,
            source_execution_succeeded=True,
            target_execution_succeeded=True,
            schema_valid=True,
            remaining_discrepancy_count=1,
            new_discrepancy_count=0,
            repair_verification_passed=None,
            dataset_unchanged=None,
            validation_config_unchanged=None,
            audit_lineage_complete=True,
        ) is False

    def test_repair_not_verified(self):
        assert determine_verified(
            translation_valid=True,
            source_execution_succeeded=True,
            target_execution_succeeded=True,
            schema_valid=True,
            remaining_discrepancy_count=0,
            new_discrepancy_count=0,
            repair_verification_passed=False,
            dataset_unchanged=True,
            validation_config_unchanged=True,
            audit_lineage_complete=True,
        ) is False

    def test_lineage_incomplete(self):
        assert determine_verified(
            translation_valid=True,
            source_execution_succeeded=True,
            target_execution_succeeded=True,
            schema_valid=True,
            remaining_discrepancy_count=0,
            new_discrepancy_count=0,
            repair_verification_passed=None,
            dataset_unchanged=None,
            validation_config_unchanged=None,
            audit_lineage_complete=False,
        ) is False

    def test_dataset_changed(self):
        assert determine_verified(
            translation_valid=True,
            source_execution_succeeded=True,
            target_execution_succeeded=True,
            schema_valid=True,
            remaining_discrepancy_count=0,
            new_discrepancy_count=0,
            repair_verification_passed=True,
            dataset_unchanged=False,
            validation_config_unchanged=True,
            audit_lineage_complete=True,
        ) is False

    def test_new_discrepancies(self):
        assert determine_verified(
            translation_valid=True,
            source_execution_succeeded=True,
            target_execution_succeeded=True,
            schema_valid=True,
            remaining_discrepancy_count=0,
            new_discrepancy_count=1,
            repair_verification_passed=True,
            dataset_unchanged=True,
            validation_config_unchanged=True,
            audit_lineage_complete=True,
        ) is False


class TestDecisionEngine:
    @pytest.fixture
    def engine(self):
        return DecisionEngine()

    def _make_evaluation(self, all_passed: bool, gate_overrides: dict | None = None) -> HardGateEvaluation:
        gates = []
        for i in range(1, 12):
            gid = f"GATE-{i:03d}"
            outcome = (gate_overrides or {}).get(gid, GateOutcome.PASS)
            gates.append(HardGateResult(gate_id=gid, gate_name=f"Gate {i}", outcome=outcome, reason="ok"))
        failed = sum(1 for g in gates if g.outcome == GateOutcome.FAIL)
        passed = sum(1 for g in gates if g.outcome == GateOutcome.PASS)
        na = sum(1 for g in gates if g.outcome == GateOutcome.NOT_APPLICABLE)
        return HardGateEvaluation(
            gates=gates, all_passed=failed == 0, total_gates=11,
            passed_count=passed, failed_count=failed, not_applicable_count=na,
        )

    def test_verified_direct_pass(self, engine):
        ev = self._make_evaluation(True)
        status, reason = engine.determine_final_status(ev, VerificationPath.DIRECT_PASS)
        assert status == MigrationFinalStatus.VERIFIED
        assert "direct validation" in reason

    def test_verified_repaired_pass(self, engine):
        ev = self._make_evaluation(True)
        status, reason = engine.determine_final_status(ev, VerificationPath.REPAIRED_PASS)
        assert status == MigrationFinalStatus.VERIFIED
        assert "re-validation" in reason

    def test_blocked_semantic_issue(self, engine):
        ev = self._make_evaluation(False, {"GATE-011": GateOutcome.FAIL})
        status, reason = engine.determine_final_status(ev, VerificationPath.REPAIRED_PASS)
        assert status == MigrationFinalStatus.BLOCKED
        assert "GATE-011" in reason

    def test_failed_execution(self, engine):
        ev = self._make_evaluation(False, {"GATE-001": GateOutcome.FAIL})
        status, reason = engine.determine_final_status(ev, VerificationPath.DIRECT_PASS)
        assert status == MigrationFinalStatus.FAILED

    def test_blocked_schema_mismatch(self, engine):
        ev = self._make_evaluation(False, {"GATE-004": GateOutcome.FAIL})
        status, reason = engine.determine_final_status(ev, VerificationPath.DIRECT_PASS)
        assert status == MigrationFinalStatus.BLOCKED

    def test_score_does_not_override_gates(self, engine):
        """Even with 'perfect score', a failed gate produces BLOCKED."""
        ev = self._make_evaluation(False, {"GATE-011": GateOutcome.FAIL})
        status, _ = engine.determine_final_status(ev, VerificationPath.DIRECT_PASS)
        assert status != MigrationFinalStatus.VERIFIED
