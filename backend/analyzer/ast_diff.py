"""AST structural diff — classifies semantic differences between two SQLAnalysis objects."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from backend.analyzer.models import SQLAnalysis


class DiffCategory(str, Enum):
    JOIN_TYPE_CHANGED = "JOIN_TYPE_CHANGED"
    JOIN_CONDITION_CHANGED = "JOIN_CONDITION_CHANGED"
    FILTER_CHANGED = "FILTER_CHANGED"
    FILTER_ADDED = "FILTER_ADDED"
    FILTER_REMOVED = "FILTER_REMOVED"
    OPERATOR_CHANGED = "OPERATOR_CHANGED"
    AGGREGATION_CHANGED = "AGGREGATION_CHANGED"
    AGGREGATION_ADDED = "AGGREGATION_ADDED"
    AGGREGATION_REMOVED = "AGGREGATION_REMOVED"
    CASE_RULE_CHANGED = "CASE_RULE_CHANGED"
    NULL_SEMANTICS_CHANGED = "NULL_SEMANTICS_CHANGED"
    TABLE_ADDED = "TABLE_ADDED"
    TABLE_REMOVED = "TABLE_REMOVED"
    COLUMN_ADDED = "COLUMN_ADDED"
    COLUMN_REMOVED = "COLUMN_REMOVED"


class DiffItem(BaseModel):
    category: DiffCategory
    source_value: Any = None
    target_value: Any = None
    detail: str = ""


class StructuralDiff(BaseModel):
    source_hash: str
    target_hash: str
    diffs: list[DiffItem] = Field(default_factory=list)
    is_identical: bool = True


def compare_analyses(source: SQLAnalysis, target: SQLAnalysis) -> StructuralDiff:
    """Compute a structured diff between two analysis results."""
    diffs: list[DiffItem] = []

    _diff_tables(source, target, diffs)
    _diff_joins(source, target, diffs)
    _diff_filters(source, target, diffs)
    _diff_aggregations(source, target, diffs)
    _diff_business_rules(source, target, diffs)
    _diff_null_semantics(source, target, diffs)

    return StructuralDiff(
        source_hash=source.sql_hash,
        target_hash=target.sql_hash,
        diffs=diffs,
        is_identical=len(diffs) == 0,
    )


# ── diff helpers ────────────────────────────────────────────────────────────


def _diff_tables(s: SQLAnalysis, t: SQLAnalysis, diffs: list[DiffItem]) -> None:
    src_names = {tbl.name for tbl in s.tables}
    tgt_names = {tbl.name for tbl in t.tables}
    for name in src_names - tgt_names:
        diffs.append(
            DiffItem(
                category=DiffCategory.TABLE_REMOVED,
                source_value=name,
                detail=f"Table '{name}' removed",
            )
        )
    for name in tgt_names - src_names:
        diffs.append(
            DiffItem(
                category=DiffCategory.TABLE_ADDED, target_value=name, detail=f"Table '{name}' added"
            )
        )


def _diff_joins(s: SQLAnalysis, t: SQLAnalysis, diffs: list[DiffItem]) -> None:
    for i, sj in enumerate(s.joins):
        if i < len(t.joins):
            tj = t.joins[i]
            if sj.join_type != tj.join_type:
                diffs.append(
                    DiffItem(
                        category=DiffCategory.JOIN_TYPE_CHANGED,
                        source_value=sj.join_type,
                        target_value=tj.join_type,
                        detail=f"Join {sj.id}: type changed {sj.join_type} → {tj.join_type}",
                    )
                )
            if sj.condition != tj.condition:
                diffs.append(
                    DiffItem(
                        category=DiffCategory.JOIN_CONDITION_CHANGED,
                        source_value=sj.condition,
                        target_value=tj.condition,
                        detail=f"Join {sj.id}: condition changed",
                    )
                )


def _diff_filters(s: SQLAnalysis, t: SQLAnalysis, diffs: list[DiffItem]) -> None:
    src_exprs = {f.expression for f in s.filters}
    tgt_exprs = {f.expression for f in t.filters}
    for expr in src_exprs - tgt_exprs:
        diffs.append(
            DiffItem(
                category=DiffCategory.FILTER_REMOVED,
                source_value=expr,
                detail=f"Filter removed: {expr}",
            )
        )
    for expr in tgt_exprs - src_exprs:
        diffs.append(
            DiffItem(
                category=DiffCategory.FILTER_ADDED,
                target_value=expr,
                detail=f"Filter added: {expr}",
            )
        )
    # check for operator changes in remaining filters
    for sf in s.filters:
        for tf in t.filters:
            if sf.scope == tf.scope and sf.expression != tf.expression:
                # heuristic: if they share similar structure but differ in operator
                for op in (">", ">=", "<", "<=", "=", "!="):
                    if op in sf.expression and op not in tf.expression:
                        diffs.append(
                            DiffItem(
                                category=DiffCategory.OPERATOR_CHANGED,
                                source_value=sf.expression,
                                target_value=tf.expression,
                                detail="Possible operator change in filter",
                            )
                        )
                        break


def _diff_aggregations(s: SQLAnalysis, t: SQLAnalysis, diffs: list[DiffItem]) -> None:
    src_keys = {(a.function, a.expression) for a in s.aggregations}
    tgt_keys = {(a.function, a.expression) for a in t.aggregations}
    for key in src_keys - tgt_keys:
        diffs.append(
            DiffItem(
                category=DiffCategory.AGGREGATION_REMOVED,
                source_value=f"{key[0]}({key[1]})",
                detail="Aggregation removed",
            )
        )
    for key in tgt_keys - src_keys:
        diffs.append(
            DiffItem(
                category=DiffCategory.AGGREGATION_ADDED,
                target_value=f"{key[0]}({key[1]})",
                detail="Aggregation added",
            )
        )
    # distinct changes
    for sa in s.aggregations:
        for ta in t.aggregations:
            if (
                sa.function == ta.function
                and sa.expression == ta.expression
                and sa.distinct != ta.distinct
            ):
                diffs.append(
                    DiffItem(
                        category=DiffCategory.AGGREGATION_CHANGED,
                        source_value=f"distinct={sa.distinct}",
                        target_value=f"distinct={ta.distinct}",
                        detail=f"{sa.function}({sa.expression}) distinct flag changed",
                    )
                )


def _diff_business_rules(s: SQLAnalysis, t: SQLAnalysis, diffs: list[DiffItem]) -> None:
    for i, sr in enumerate(s.business_rules):
        if i < len(t.business_rules):
            tr = t.business_rules[i]
            if sr.condition != tr.condition or sr.then != tr.then:
                diffs.append(
                    DiffItem(
                        category=DiffCategory.CASE_RULE_CHANGED,
                        source_value=sr.model_dump(),
                        target_value=tr.model_dump(),
                        detail=f"Business rule {sr.id} changed",
                    )
                )


def _diff_null_semantics(s: SQLAnalysis, t: SQLAnalysis, diffs: list[DiffItem]) -> None:
    src_kinds = {(n.expression, n.kind) for n in s.null_sensitive_expressions}
    tgt_kinds = {(n.expression, n.kind) for n in t.null_sensitive_expressions}
    if src_kinds != tgt_kinds:
        diffs.append(
            DiffItem(
                category=DiffCategory.NULL_SEMANTICS_CHANGED,
                source_value=str(src_kinds),
                target_value=str(tgt_kinds),
                detail="NULL-sensitive expressions differ between source and target",
            )
        )
