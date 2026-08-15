"""Validation helpers for evidence sampling and report serialization."""

from typing import Any

from backend.validation.models import EvidenceItem


def truncate_evidence(
    evidence_items: list[EvidenceItem],
    max_items: int = 100,
) -> tuple[list[EvidenceItem], bool]:
    """Truncate evidence items deterministically to max_items limit."""
    if len(evidence_items) <= max_items:
        return evidence_items, False
    return evidence_items[:max_items], True


def format_validation_summary(report_dict: dict[str, Any]) -> str:
    """Format human-readable CLI summary of a ValidationReport."""
    lines = [
        "MIGRA-Q SEMANTIC VALIDATION",
        "==========================",
        f"Validation ID : {report_dict.get('validation_id')}",
        f"Source Exec ID: {report_dict.get('source_execution_id')}",
        f"Target Exec ID: {report_dict.get('target_execution_id')}",
        f"Dataset ID    : {report_dict.get('dataset_id')}",
        f"Overall Status: {report_dict.get('overall_status')}",
        "",
        "CHECKS DETAIL:",
    ]
    for chk in report_dict.get("checks", []):
        lines.append(
            f"  - {chk.get('check_name'):<22}: {chk.get('status'):<7} "
            f"(Score: {chk.get('score'):.2f}, Mismatches: {chk.get('mismatch_count')})"
        )
    lines.append("")
    summary = report_dict.get("summary", {})
    lines.append(
        f"Summary: {summary.get('checks_run')} run, {summary.get('checks_passed')} passed, "
        f"{summary.get('checks_failed')} failed, {summary.get('checks_errored')} errored."
    )
    return "\n".join(lines)
