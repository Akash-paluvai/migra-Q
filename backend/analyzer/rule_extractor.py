"""Rule extractor — walks a SQLGlot AST and extracts structured analysis components."""

from __future__ import annotations

from sqlglot import exp

from backend.analyzer.models import (
    AggregationInfo,
    AnalysisWarning,
    BusinessRule,
    CaseExpression,
    CaseWhen,
    ColumnRef,
    FilterInfo,
    JoinInfo,
    NullSensitiveExpr,
    TableRef,
)

# ── counters (per-analysis, reset by caller) ────────────────────────────────

_counters: dict[str, int] = {}


def _next_id(prefix: str) -> str:
    _counters[prefix] = _counters.get(prefix, 0) + 1
    return f"{prefix}-{_counters[prefix]:03d}"


def _reset_counters() -> None:
    _counters.clear()


# ── tables ──────────────────────────────────────────────────────────────────


def extract_tables(tree: exp.Expression) -> list[TableRef]:
    seen: set[str] = set()
    tables: list[TableRef] = []
    for tbl in tree.find_all(exp.Table):
        name = tbl.name
        alias = tbl.alias if tbl.alias else None
        key = f"{name}|{alias}"
        if key not in seen:
            seen.add(key)
            tables.append(TableRef(name=name, alias=alias))
    return tables


# ── columns ─────────────────────────────────────────────────────────────────


def extract_columns(tree: exp.Expression) -> list[ColumnRef]:
    cols: list[ColumnRef] = []
    seen: set[str] = set()

    for col in tree.find_all(exp.Column):
        tbl = col.table or None
        name = col.name
        ctx = _column_context(col)
        key = f"{tbl}|{name}|{ctx}"
        if key not in seen:
            seen.add(key)
            cols.append(ColumnRef(name=name, table=tbl if tbl else None, context=ctx))
    return cols


def _column_context(col: exp.Column) -> str:
    parent = col.parent
    while parent is not None:
        if isinstance(parent, exp.Where):
            return "filter"
        if isinstance(parent, exp.Having):
            return "having"
        if isinstance(parent, exp.Join):
            return "join"
        if isinstance(parent, exp.Group):
            return "group_by"
        if isinstance(parent, exp.Order):
            return "order_by"
        if isinstance(parent, exp.AggFunc):
            return "aggregate"
        if isinstance(parent, exp.Select):
            return "select"
        parent = parent.parent
    return "other"


# ── joins ───────────────────────────────────────────────────────────────────


def extract_joins(tree: exp.Expression) -> list[JoinInfo]:
    joins: list[JoinInfo] = []
    for join_node in tree.find_all(exp.Join):
        # In sqlglot v30, join type is in 'side' and/or 'kind' args
        side = join_node.args.get("side", "") or ""
        kind = join_node.args.get("kind", "") or ""
        join_type = f"{side} {kind}".strip().upper()
        if not join_type or join_type == "JOIN":
            join_type = "INNER"

        on_clause = join_node.args.get("on")
        condition = on_clause.sql() if on_clause else ""

        left_col, right_col = _parse_join_sides(on_clause)
        joins.append(
            JoinInfo(
                id=_next_id("JOIN"),
                join_type=join_type,
                left=left_col,
                right=right_col,
                condition=condition,
            )
        )
    return joins


def _parse_join_sides(on_clause: exp.Expression | None) -> tuple[str, str]:
    if on_clause is None:
        return ("", "")
    if isinstance(on_clause, exp.EQ):
        return (on_clause.left.sql(), on_clause.right.sql())
    return (on_clause.sql(), "")


# ── filters ─────────────────────────────────────────────────────────────────


def extract_filters(tree: exp.Expression) -> list[FilterInfo]:
    filters: list[FilterInfo] = []
    where = tree.find(exp.Where)
    if where and where.this:
        for pred in _flatten_predicates(where.this):
            filters.append(FilterInfo(id=_next_id("FILTER"), scope="WHERE", expression=pred.sql()))

    having = tree.find(exp.Having)
    if having and having.this:
        for pred in _flatten_predicates(having.this):
            filters.append(FilterInfo(id=_next_id("FILTER"), scope="HAVING", expression=pred.sql()))
    return filters


def _flatten_predicates(node: exp.Expression) -> list[exp.Expression]:
    """Yield leaf predicates from AND trees; keep OR as a single expression."""
    if isinstance(node, exp.And):
        return _flatten_predicates(node.left) + _flatten_predicates(node.right)
    if isinstance(node, exp.Or):
        return [node]
    return [node]


# ── aggregations ────────────────────────────────────────────────────────────


def extract_aggregations(tree: exp.Expression) -> list[AggregationInfo]:
    aggs: list[AggregationInfo] = []
    group_by_cols: list[str] = []
    group = tree.find(exp.Group)
    if group:
        group_by_cols = [e.sql() for e in group.expressions]

    seen: set[str] = set()
    for agg_node in tree.find_all(exp.AggFunc):
        func_name = type(agg_node).__name__.upper()
        func_map = {"COUNT": "COUNT", "SUM": "SUM", "AVG": "AVG", "MIN": "MIN", "MAX": "MAX"}
        func_name = func_map.get(func_name, func_name)

        is_distinct = bool(agg_node.args.get("distinct"))
        if isinstance(agg_node.this, exp.Distinct):
            is_distinct = True
            if agg_node.this.expressions:
                inner = ", ".join(e.sql() for e in agg_node.this.expressions)
            elif agg_node.this.this:
                inner = agg_node.this.this.sql()
            else:
                inner = "*"
        else:
            inner = agg_node.this.sql() if agg_node.this else "*"

        key = f"{func_name}|{inner}|{is_distinct}"
        if key not in seen:
            seen.add(key)
            aggs.append(
                AggregationInfo(
                    id=_next_id("AGG"),
                    function=func_name,
                    expression=inner,
                    distinct=is_distinct,
                    group_by=group_by_cols,
                )
            )
    return aggs


# ── CASE expressions and business rules ─────────────────────────────────────


def extract_case_expressions(
    tree: exp.Expression,
) -> tuple[list[CaseExpression], list[BusinessRule]]:
    cases: list[CaseExpression] = []
    rules: list[BusinessRule] = []

    for case_node in tree.find_all(exp.Case):
        whens: list[CaseWhen] = []
        for if_node in case_node.args.get("ifs", []):
            cond = if_node.this.sql() if if_node.this else ""
            result = if_node.args.get("true")
            result_str = result.sql() if result else ""
            whens.append(CaseWhen(condition=cond, result=result_str))

        else_val = case_node.args.get("default")
        else_str = else_val.sql() if else_val else None

        case_id = _next_id("CASE")
        cases.append(CaseExpression(id=case_id, whens=whens, else_result=else_str))

        for i, w in enumerate(whens):
            rule_id = _next_id("RULE")
            cond_dict = _parse_condition(w.condition)
            rules.append(
                BusinessRule(
                    id=rule_id,
                    type=cond_dict.get("type", "expression"),
                    condition=cond_dict,
                    then=w.result,
                    else_val=else_str if i == len(whens) - 1 else None,
                )
            )

    return cases, rules


def _parse_condition(cond_sql: str) -> dict:
    """Best-effort parse of a comparison condition string."""
    for op in (">=", "<=", "!=", "<>", ">", "<", "="):
        if op in cond_sql:
            parts = cond_sql.split(op, 1)
            return {
                "type": "comparison",
                "operator": op,
                "left": parts[0].strip(),
                "right": parts[1].strip(),
            }
    upper = cond_sql.upper()
    if "IS NOT NULL" in upper:
        return {
            "type": "null_check",
            "operator": "IS NOT NULL",
            "left": cond_sql.split("IS")[0].strip(),
            "right": "",
        }
    if "IS NULL" in upper:
        return {
            "type": "null_check",
            "operator": "IS NULL",
            "left": cond_sql.split("IS")[0].strip(),
            "right": "",
        }
    return {"type": "expression", "expression": cond_sql}


# ── NULL-sensitive expressions ──────────────────────────────────────────────


def extract_null_sensitive(tree: exp.Expression) -> list[NullSensitiveExpr]:
    items: list[NullSensitiveExpr] = []

    # IS NULL / IS NOT NULL
    for node in tree.find_all(exp.Is):
        items.append(NullSensitiveExpr(id=_next_id("NULL"), expression=node.sql(), kind="IS_NULL"))

    # NOT IS NULL → IS NOT NULL (sqlglot v30 wraps with Not)
    for node in tree.find_all(exp.Not):
        inner = node.this
        if isinstance(inner, exp.Is):
            items.append(
                NullSensitiveExpr(id=_next_id("NULL"), expression=node.sql(), kind="IS_NOT_NULL")
            )

    # COALESCE
    for node in tree.find_all(exp.Coalesce):
        items.append(NullSensitiveExpr(id=_next_id("NULL"), expression=node.sql(), kind="COALESCE"))

    # NULLIF
    for node in tree.find_all(exp.Nullif):
        items.append(NullSensitiveExpr(id=_next_id("NULL"), expression=node.sql(), kind="NULLIF"))

    return items


# ── unsupported construct warnings ──────────────────────────────────────────

_UNSUPPORTED = (exp.SetOperation, exp.Subquery, exp.Window, exp.Pivot, exp.Lateral)


def detect_warnings(tree: exp.Expression) -> list[AnalysisWarning]:
    warnings: list[AnalysisWarning] = []
    for node in tree.walk():
        if isinstance(node, _UNSUPPORTED):
            warnings.append(
                AnalysisWarning(
                    code="UNSUPPORTED_CONSTRUCT",
                    message=f"Construct '{type(node).__name__}' is not fully supported in Phase 1.",
                    location=node.sql()[:80],
                )
            )
    # NULL-sensitive advisory warning
    has_null = tree.find(exp.Is) or tree.find(exp.Coalesce) or tree.find(exp.Nullif)
    if has_null:
        warnings.append(
            AnalysisWarning(
                code="NULL_SENSITIVE",
                message="Expression contains NULL-sensitive semantics.",
            )
        )
    return warnings
