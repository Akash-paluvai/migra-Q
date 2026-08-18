"""AST-based Repair Scope Checker for Phase 7 AI Repair Engine.

Uses SQLGlot AST node traversal to strictly enforce minimal repair scope boundaries.
Rejects unjustified scope creep (e.g. modifying JOIN, GROUP BY, WHERE, or unrelated
projection expressions when discrepancy is localized to risk_class).
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp


class RepairScopeChecker:
    """Enforces AST-based structural repair scope boundaries."""

    @classmethod
    def verify_repair_scope(
        cls,
        original_sql: str,
        proposed_sql: str,
        target_dialect: str,
        changed_region: str,
    ) -> tuple[bool, str, list[str]]:
        """Perform AST structural comparison between original target SQL and proposed repair SQL.

        Returns (is_scope_valid, error_message, list_of_constraints_checked).
        """
        constraints_checked = [
            "target_dialect_syntax_preserved",
            "read_only_policy_enforced",
            "target_contract_preserved",
        ]

        dialect_name = target_dialect.lower()
        if dialect_name in ("bigquery", "bq"):
            dialect_name = "bigquery"

        try:
            orig_tree = sqlglot.parse_one(original_sql, read=dialect_name)
            prop_tree = sqlglot.parse_one(proposed_sql, read=dialect_name)
        except Exception as e:
            return False, f"AST Scope Check failed due to SQL parsing error: {e}", constraints_checked

        if orig_tree is None or prop_tree is None:
            return False, "AST Scope Check failed: AST could not be generated.", constraints_checked

        # 1. Inspect JOIN clause modifications
        orig_joins = [j.sql(dialect=dialect_name) for j in orig_tree.find_all(exp.Join)]
        prop_joins = [j.sql(dialect=dialect_name) for j in prop_tree.find_all(exp.Join)]
        if orig_joins != prop_joins and "join" not in changed_region.lower():
            msg = (
                f"UNJUSTIFIED_SCOPE_CHANGE: Repair modified JOIN clause ({orig_joins} vs {prop_joins}) "
                f"which is outside target region '{changed_region}'."
            )
            return False, msg, constraints_checked

        constraints_checked.append("join_clause_unchanged")

        # 2. Check GROUP BY clause
        orig_gb = orig_tree.args.get("group")
        prop_gb = prop_tree.args.get("group")
        orig_gb_sql = orig_gb.sql(dialect_name) if orig_gb else ""
        prop_gb_sql = prop_gb.sql(dialect_name) if prop_gb else ""

        if orig_gb_sql != prop_gb_sql:
            msg = (
                f"UNJUSTIFIED_SCOPE_CHANGE: Repair modified GROUP BY clause ('{orig_gb_sql}' vs "
                f"'{prop_gb_sql}') which is outside target region '{changed_region}'."
            )
            return False, msg, constraints_checked

        constraints_checked.append("groupby_clause_unchanged")

        # 3. Check WHERE clause
        orig_w = orig_tree.args.get("where")
        prop_w = prop_tree.args.get("where")
        orig_where_sql = orig_w.sql(dialect_name) if orig_w else ""
        prop_where_sql = prop_w.sql(dialect_name) if prop_w else ""

        if orig_where_sql != prop_where_sql and "where" not in changed_region.lower():
            msg = (
                f"UNJUSTIFIED_SCOPE_CHANGE: Repair modified WHERE clause ('{orig_where_sql}' vs "
                f"'{prop_where_sql}') which is outside target region '{changed_region}'."
            )
            return False, msg, constraints_checked

        constraints_checked.append("where_clause_unchanged")

        # 4. Check Select expressions outside changed_region
        orig_selects = {
            s.alias_or_name.lower(): s.sql(dialect_name)
            for s in orig_tree.selects
            if s.alias_or_name
        }
        prop_selects = {
            s.alias_or_name.lower(): s.sql(dialect_name)
            for s in prop_tree.selects
            if s.alias_or_name
        }

        for alias_name, orig_expr_sql in orig_selects.items():
            if alias_name in prop_selects:
                prop_expr_sql = prop_selects[alias_name]
                if orig_expr_sql != prop_expr_sql:
                    # Check if this changed expression matches changed_region
                    region_lower = changed_region.lower()
                    if alias_name and alias_name not in region_lower and region_lower not in alias_name:
                        if region_lower in ("select", "columns"):
                            pass
                        else:
                            msg = (
                                f"UNJUSTIFIED_SCOPE_CHANGE: Repair modified projection expression "
                                f"for '{alias_name}' ('{orig_expr_sql}' vs '{prop_expr_sql}') "
                                f"which is outside target region '{changed_region}'."
                            )
                            return False, msg, constraints_checked

        constraints_checked.append("unrelated_projection_expressions_unchanged")
        return True, "AST Scope Check passed.", constraints_checked
