"""Structural AST diff preview utility for Phase 6 Translation Engine.

Performs structural comparison between Source SQL and Candidate Target SQL.
Does NOT perform semantic validation.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

from backend.analyzer.service import analyze


def generate_diff_preview(
    source_sql: str,
    source_dialect: str,
    target_sql: str,
    target_dialect: str,
) -> tuple[int, int, list[str]]:
    """Compare source SQL AST and candidate target SQL AST to extract structural differences.

    Returns (source_rule_count, target_rule_count, list_of_structural_differences).
    """
    diffs: list[str] = []

    # Parse source via Phase 1 Analyzer
    try:
        src_analysis = analyze(sql=source_sql, dialect=source_dialect)
        src_rules = src_analysis.business_rules
        src_rule_count = len(src_rules)
    except Exception:
        src_rule_count = 0

    # Parse target via SQLGlot
    try:
        glot_target = target_dialect.lower()
        if glot_target == "teradata":
            glot_target = "teradata"
        elif glot_target in ("bigquery", "bq"):
            glot_target = "bigquery"

        tgt_tree = sqlglot.parse_one(target_sql, read=glot_target)
        wheres = len(list(tgt_tree.find_all(exp.Where)))
        cases = len(list(tgt_tree.find_all(exp.Case)))
        tgt_rule_count = wheres + cases
    except Exception:
        tgt_rule_count = 0
        tgt_tree = None

    if tgt_tree is None:
        return src_rule_count, tgt_rule_count, ["Candidate SQL could not be parsed for AST diff."]

    # Inspect source vs target GROUP BY columns
    try:
        src_tree = sqlglot.parse_one(source_sql, read=source_dialect)
        src_groupby = set()
        src_gb_node = src_tree.find(exp.Group)
        if src_gb_node:
            src_groupby = {col.name.lower() for col in src_gb_node.find_all(exp.Column) if col.name}

        tgt_groupby = set()
        tgt_gb_node = tgt_tree.find(exp.Group)
        if tgt_gb_node:
            tgt_groupby = {col.name.lower() for col in tgt_gb_node.find_all(exp.Column) if col.name}

        if src_groupby != tgt_groupby:
            diffs.append(
                f"GROUP BY columns changed: source ({', '.join(sorted(src_groupby))}) "
                f"vs target ({', '.join(sorted(tgt_groupby))})"
            )
    except Exception:
        pass

    # Inspect ORDER BY clause addition
    src_has_order = False
    if "src_tree" in locals() and src_tree:
        src_has_order = src_tree.find(exp.Order) is not None
    tgt_has_order = tgt_tree.find(exp.Order) is not None
    if not src_has_order and tgt_has_order:
        diffs.append("ORDER BY clause added in candidate target SQL")

    # Inspect CASE expression aggregation changes
    tgt_cases = list(tgt_tree.find_all(exp.Case))
    for c in tgt_cases:
        if list(c.find_all(exp.AggFunc)):
            diffs.append("Aggregation function (e.g. SUM) introduced inside CASE expression")
            break

    return src_rule_count, tgt_rule_count, diffs
