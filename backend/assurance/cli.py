"""Phase 9 Assurance CLI — formatted report output.

Usage:
    python -m backend.assurance.cli report --migration-id <id>
"""

from __future__ import annotations

import argparse
import sys

from backend.assurance.models import MigrationAssuranceReport
from backend.assurance.service import MigrationAssuranceService


def format_report(report: MigrationAssuranceReport) -> str:
    """Format a MigrationAssuranceReport for terminal output."""
    lines: list[str] = []
    lines.append("MIGRA-Q MIGRATION ASSURANCE")
    lines.append("────────────────────────────────────")
    lines.append("")
    lines.append("")
    lines.append(f"Migration: {report.migration_id}")
    if report.translation_summary:
        lines.append(f"Source: {report.translation_summary.source_dialect.capitalize()}")
        lines.append(f"Target: {report.translation_summary.target_dialect.capitalize()}")
    if report.metadata.get("profile"):
        lines.append(f"Profile: {report.metadata['profile']}")
    lines.append("")
    lines.append("")
    lines.append("Initial validation:")
    init_val = report.validation_summary.overall_status if report.validation_summary else "N/A"
    lines.append(f"{init_val}")
    lines.append("")
    lines.append("")
    lines.append("Discrepancies:")
    disc_cnt = report.discrepancy_summary.discrepancy_count if report.discrepancy_summary else 0
    lines.append(f"{disc_cnt}")
    lines.append("")
    lines.append("")
    lines.append("Affected records:")
    aff_cnt = report.discrepancy_summary.total_affected_rows if report.discrepancy_summary else 0
    lines.append(f"{aff_cnt:,}")
    lines.append("")
    lines.append("")
    lines.append("Repair:")
    rep_stat = report.verification_summary.status if report.verification_summary and report.verification_summary.verification_id else "NOT_ATTEMPTED"
    lines.append(f"{rep_stat}")
    lines.append("")
    lines.append("")
    lines.append("Before:")
    bef_cnt = report.verification_summary.affected_rows_before if report.verification_summary and report.verification_summary.verification_id else aff_cnt
    lines.append(f"{bef_cnt:,}")
    lines.append("")
    lines.append("")
    lines.append("After:")
    aft_cnt = report.verification_summary.affected_rows_after if report.verification_summary and report.verification_summary.verification_id else 0
    lines.append(f"{aft_cnt:,}")
    lines.append("")
    lines.append("")
    lines.append("New discrepancies:")
    new_cnt = report.verification_summary.new_discrepancy_count if report.verification_summary and report.verification_summary.verification_id else 0
    lines.append(f"{new_cnt}")
    lines.append("")
    lines.append("")
    lines.append("Assurance score:")
    lines.append(f"{report.score.evidence_score:.1f} / 100")
    lines.append("")
    lines.append("")
    lines.append("Evidence coverage:")
    lines.append(f"{report.score.evidence_coverage:.0f}%")
    skipped_names = [c.name for c in report.score.components if c.status.value == "NOT_APPLICABLE"]
    if skipped_names:
        skipped_str = ", ".join(skipped_names)
        lines.append(f"Why: {skipped_str} was SKIPPED in this run.")
    lines.append("")
    lines.append("")
    lines.append("Hard gates:")
    p_cnt = report.gate_evaluation.passed_count
    na_cnt = report.gate_evaluation.not_applicable_count
    f_cnt = report.gate_evaluation.failed_count
    lines.append(f"{p_cnt} PASS, {na_cnt} NOT APPLICABLE, {f_cnt} FAIL")
    lines.append("")
    lines.append("")
    lines.append("Verification path:")
    lines.append(f"{report.verification_path.value}")
    lines.append("")
    lines.append("")
    lines.append("FINAL STATUS:")
    icon = "✓" if report.final_status.value == "VERIFIED" else "✗"
    lines.append(f"{icon} {report.final_status.value}")
    lines.append("")
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
