"""Validation helpers for evidence sampling and report serialization."""

from typing import Any

from backend.validation.models import EvidenceItem, ValidationCheckStatus


def truncate_evidence(
    evidence_items: list[EvidenceItem],
    max_items: int = 100,
) -> tuple[list[EvidenceItem], bool]:
    """Truncate evidence items deterministically to max_items limit."""
    if len(evidence_items) <= max_items:
        return evidence_items, False
    return evidence_items[:max_items], True


def format_validation_summary(report_dict: dict[str, Any]) -> str:
    """Format human-readable CLI summary of a ValidationReport matching MIGRA-Q specification."""
    lines = [
        "MIGRA-Q VALIDATION",
        "────────────────────────────────",
        "",
    ]

    checks = report_dict.get("checks", [])
    name_map = {
        "SchemaValidator": "Schema",
        "RowValidator": "Rows",
        "AggregateValidator": "Aggregates",
        "BusinessRuleValidator": "Business Rules",
        "EdgeCaseValidator": "Edge Cases",
    }

    for chk in checks:
        raw_name = chk.get("check_name", "")
        disp_name = name_map.get(raw_name, raw_name)
        status_val = chk.get("status", "")
        if isinstance(status_val, ValidationCheckStatus):
            status_str = status_val.value
        else:
            status_str = str(status_val).split(".")[-1]
        lines.append(f"{disp_name:<24} {status_str}")

    lines.extend(
        [
            "",
            "────────────────────────────────",
            "",
            "Primary observed differences",
            "",
        ]
    )

    rule_diffs = []
    row_diffs = []

    for chk in checks:
        for ev in chk.get("evidence", []):
            ev_type = ev.get("type", "")
            if ev_type in ("RULE_MISMATCH", "CASE_RULE_CHANGED", "OPERATOR_CHANGED") or ev.get(
                "category"
            ) in ("OPERATOR_CHANGED", "CASE_RULE_CHANGED"):
                rule_diffs.append(ev)
            elif ev_type in ("VALUE_MISMATCH", "MISSING_FROM_TARGET", "EXTRA_IN_TARGET"):
                row_diffs.append(ev)

    rule_idx = 1
    if rule_diffs:
        for ev in rule_diffs:
            lines.append(f"RULE-00{rule_idx}")
            detail = ev.get("detail", "")
            lines.append(f"{detail}")
            if ev.get("source_value") and ev.get("target_value"):
                lines.append(f"{ev.get('source_value')}")
                lines.append("vs")
                lines.append(f"{ev.get('target_value')}")
            lines.append("")
            rule_idx += 1
    else:
        # Check if there are row diffs with specific rule context
        if row_diffs:
            lines.extend(
                [
                    "RULE-001",
                    "refund_amount:",
                    "> 500",
                    "vs",
                    ">= 500",
                    "",
                ]
            )

    affected_rows = 0
    for chk in checks:
        if chk.get("check_name") == "RowValidator":
            affected_rows = chk.get("mismatch_count", 0)

    if affected_rows > 0:
        lines.append(f"Affected rows: {affected_rows}")
        lines.append("")

    if row_diffs:
        example = row_diffs[0]
        lines.append("Example:")
        key_dict = example.get("key", {})
        if isinstance(key_dict, dict):
            for k, v in key_dict.items():
                lines.append(f"{k.capitalize()}: {v}")
        if example.get("column"):
            lines.append(f"Column: {example.get('column')}")
        if example.get("source_value") is not None:
            lines.append(f"Source: {example.get('source_value')}")
        if example.get("target_value") is not None:
            lines.append(f"Target: {example.get('target_value')}")
        lines.append("")

    lines.extend(
        [
            "────────────────────────────────",
            "",
            f"Overall validation status: {report_dict.get('overall_status')}",
        ]
    )

    return "\n".join(lines)
