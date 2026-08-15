"""CLI summary formatting helpers for Phase 5 discrepancy reports."""

from typing import Any


def format_discrepancy_summary(report_dict: dict[str, Any]) -> str:
    """Format human-readable CLI output for a DiscrepancyReport."""
    lines = [
        "MIGRA-Q DISCREPANCY ANALYSIS",
        "============================",
        f"Diagnosis ID : {report_dict.get('diagnosis_id')}",
        f"Validation ID: {report_dict.get('validation_id')}",
        f"Version      : {report_dict.get('classifier_version')}",
        "",
    ]

    discrepancies = report_dict.get("discrepancies", [])
    if not discrepancies:
        lines.append("No distinct semantic discrepancies detected.")
        return "\n".join(lines)

    for d in discrepancies:
        disc_id = d.get("discrepancy_id", "")
        cat = d.get("category", "")
        sev = d.get("severity", "")
        conf = d.get("classification_confidence", 1.0)
        src_expr = d.get("source_expression") or "N/A"
        tgt_expr = d.get("target_expression") or "N/A"
        affected_rows = d.get("affected_row_count", 0)

        cat_val = getattr(cat, "value", str(cat))
        if "." in cat_val:
            cat_val = cat_val.split(".")[-1]

        sev_val = getattr(sev, "value", str(sev))
        if "." in sev_val:
            sev_val = sev_val.split(".")[-1]

        method = d.get("classification_method", "")
        method_val = getattr(method, "value", str(method))
        if "." in method_val:
            method_val = method_val.split(".")[-1]

        lines.extend(
            [
                f"{disc_id}",
                "────────────────────────────────────",
                f"Category:            {cat_val}",
                f"Severity:            {sev_val}",
                f"Confidence:          {conf:.2f}",
                f"Classification:      {method_val}",
                f"Source expression:   {src_expr}",
                f"Target expression:   {tgt_expr}",
                f"Analysis path:       {d.get('analysis_path')}",
                f"Impact:              {affected_rows} affected rows",
                "",
                "Evidence:",
            ]
        )

        for ev in d.get("evidence", []):
            detail = ev.get("detail", "")
            col = ev.get("column")
            col_str = f" ({col})" if col else ""
            lines.append(f"  ✓ {detail}{col_str}")

        lines.extend(
            [
                "",
                "Reason:",
                f"  {d.get('classification_reason')}",
                "",
            ]
        )

    return "\n".join(lines)
