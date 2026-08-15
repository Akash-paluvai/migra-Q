"""Phase 9 Assurance CLI — formatted report output.

Usage:
    python -m backend.assurance.cli report --migration-id <id>
"""

from __future__ import annotations

import argparse
import sys

from backend.assurance.models import GateOutcome, MigrationAssuranceReport
from backend.assurance.service import MigrationAssuranceService


def format_report(report: MigrationAssuranceReport) -> str:
    """Format a MigrationAssuranceReport for terminal output."""
    lines: list[str] = []
    lines.append("")
    lines.append("=" * 50)
    lines.append("MIGRA-Q MIGRATION ASSURANCE REPORT")
    lines.append("=" * 50)
    lines.append(f"Migration ID:       {report.migration_id}")
    lines.append(f"Assurance Version:  {report.assurance_version}")
    lines.append(f"Created At:         {report.created_at}")
    lines.append(f"Verification Path:  {report.verification_path.value}")
    lines.append("")

    # Score section
    lines.append("ASSURANCE")
    lines.append("─" * 40)
    lines.append(f"Evidence Score        {report.score.evidence_score:>6.1f}")
    lines.append(f"Evidence Coverage     {report.score.evidence_coverage:>5.1f}%")
    lines.append(f"Hard Gates            {report.gate_evaluation.passed_count + report.gate_evaluation.not_applicable_count:>2} / {report.gate_evaluation.total_gates}")
    remaining = 0
    if report.discrepancy_summary:
        remaining = report.discrepancy_summary.discrepancy_count
    if report.verification_summary and report.verification_summary.verification_id:
        remaining = report.verification_summary.remaining_discrepancy_count
    lines.append(f"Unresolved Issues     {remaining:>2}")
    lines.append("")

    # Final Status
    status_icon = "✓" if report.final_status.value == "VERIFIED" else "✗"
    lines.append("Final Status")
    lines.append(f"{status_icon} {report.final_status.value}")
    lines.append("")
    lines.append(f"Decision: {report.decision_reason}")
    lines.append("")

    # Score components
    lines.append("SCORE COMPONENTS")
    lines.append("─" * 40)
    for c in report.score.components:
        status_str = c.status.value
        if c.status.value == "NOT_APPLICABLE":
            lines.append(f"  {c.name:<30} {status_str}")
        else:
            lines.append(f"  {c.name:<30} {c.raw_score:>5.1f}  (weight: {c.effective_weight:.1%})")
    lines.append("")

    # Hard gates
    lines.append("HARD GATES")
    lines.append("─" * 40)
    for g in report.gate_evaluation.gates:
        icon = "✓" if g.outcome == GateOutcome.PASS else ("─" if g.outcome == GateOutcome.NOT_APPLICABLE else "✗")
        lines.append(f"  {icon} {g.gate_id} {g.gate_name}")
    lines.append("")

    # Audit lineage
    lines.append("AUDIT LINEAGE")
    lines.append("─" * 40)
    lineage = report.lineage
    if lineage.translation_id:
        lines.append(f"  Translation ID:       {lineage.translation_id}")
    if lineage.source_execution_id:
        lines.append(f"  Source Execution ID:  {lineage.source_execution_id}")
    if lineage.target_execution_id:
        lines.append(f"  Target Execution ID:  {lineage.target_execution_id}")
    if lineage.validation_id:
        lines.append(f"  Validation ID:        {lineage.validation_id}")
    if lineage.diagnosis_id:
        lines.append(f"  Diagnosis ID:         {lineage.diagnosis_id}")
    if lineage.ai_diagnosis_id:
        lines.append(f"  AI Diagnosis ID:      {lineage.ai_diagnosis_id}")
    if lineage.repair_id:
        lines.append(f"  Repair ID:            {lineage.repair_id}")
    if lineage.verification_id:
        lines.append(f"  Verification ID:      {lineage.verification_id}")
    lines.append(f"  Lineage Complete:     {lineage.is_complete}")
    lines.append("")

    # Limitations
    if report.limitations:
        lines.append("LIMITATIONS")
        lines.append("─" * 40)
        for lim in report.limitations:
            lines.append(f"  • {lim}")
        lines.append("")

    lines.append("=" * 50)
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MIGRA-Q Phase 9 Migration Assurance CLI"
    )
    sub = parser.add_subparsers(dest="command")
    report_cmd = sub.add_parser("report", help="Print assurance report for a migration")
    report_cmd.add_argument("--migration-id", required=True, help="Migration ID")

    args = parser.parse_args()
    if args.command != "report":
        parser.print_help()
        sys.exit(1)

    service = MigrationAssuranceService()
    report = service.get_assurance_report(args.migration_id)
    if report is None:
        print(f"No assurance report found for migration: {args.migration_id}")
        sys.exit(1)

    print(format_report(report))


if __name__ == "__main__":
    main()
