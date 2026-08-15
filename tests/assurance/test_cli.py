"""Tests for Phase 9 CLI report formatting."""


from backend.assurance.cli import format_report
from backend.assurance.models import (
    AssuranceBand,
    AssuranceScore,
    AuditLineage,
    ComponentStatus,
    GateOutcome,
    HardGateEvaluation,
    HardGateResult,
    MigrationAssuranceReport,
    MigrationFinalStatus,
    ScoreComponent,
    VerificationPath,
)


class TestFormatReport:
    def test_verified_report_format(self):
        gates = [
            HardGateResult(gate_id=f"GATE-{i:03d}", gate_name=f"Gate {i}", outcome=GateOutcome.PASS, reason="ok")
            for i in range(1, 12)
        ]
        report = MigrationAssuranceReport(
            migration_id="MIG-TEST",
            final_status=MigrationFinalStatus.VERIFIED,
            verification_path=VerificationPath.REPAIRED_PASS,
            decision_reason="Verified by deterministic re-validation.",
            score=AssuranceScore(
                evidence_score=100.0,
                evidence_coverage=75.0,
                band=AssuranceBand.STRONG_EVIDENCE,
                components=[
                    ScoreComponent(name="Schema compatibility", weight=0.10, raw_score=100.0, weighted_score=13.3, effective_weight=0.133, status=ComponentStatus.SCORED, source_check="SchemaValidator"),
                ],
            ),
            gate_evaluation=HardGateEvaluation(
                gates=gates, all_passed=True, total_gates=11,
                passed_count=11, failed_count=0, not_applicable_count=0,
            ),
            lineage=AuditLineage(
                translation_id="TRN-001",
                source_execution_id="EXEC-SRC",
                target_execution_id="EXEC-TGT",
                validation_id="VAL-001",
                is_complete=True,
            ),
        )
        output = format_report(report)
        assert "MIG-TEST" in output
        assert "VERIFIED" in output
        assert "100.0 / 100" in output
        assert "75%" in output
        assert "11 PASS, 0 NOT APPLICABLE, 0 FAIL" in output
        assert "✓" in output

    def test_blocked_report_format(self):
        gates = [
            HardGateResult(gate_id="GATE-011", gate_name="No unresolved semantic discrepancies", outcome=GateOutcome.FAIL, reason="1 unresolved"),
        ]
        report = MigrationAssuranceReport(
            migration_id="MIG-BLOCKED",
            final_status=MigrationFinalStatus.BLOCKED,
            decision_reason="Migration contains unresolved issues.",
            gate_evaluation=HardGateEvaluation(
                gates=gates, all_passed=False, total_gates=1,
                passed_count=0, failed_count=1, not_applicable_count=0,
            ),
        )
        output = format_report(report)
        assert "BLOCKED" in output
        assert "✗" in output

    def test_not_applicable_gate_icon(self):
        gates = [
            HardGateResult(gate_id="GATE-007", gate_name="Repair verification", outcome=GateOutcome.NOT_APPLICABLE, reason="No repair"),
        ]
        report = MigrationAssuranceReport(
            migration_id="MIG-NA",
            gate_evaluation=HardGateEvaluation(
                gates=gates, all_passed=True, total_gates=1,
                passed_count=0, failed_count=0, not_applicable_count=1,
            ),
        )
        output = format_report(report)
        assert "─" in output  # NOT_APPLICABLE icon
