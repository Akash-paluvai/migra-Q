"""Candidate repair proposal syntax and contract preservation validator for Phase 7."""

from __future__ import annotations

import sqlglot
from sqlglot import exp


class RepairProposalValidator:
    """Validates target candidate repair SQL syntax and read-only safety policy."""

    BLOCKED_NODE_TYPES = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
        exp.Merge,
    )

    @classmethod
    def validate_repair_syntax_and_safety(
        cls,
        proposed_sql: str,
        target_dialect: str,
    ) -> tuple[bool, str]:
        """Verify proposed repair SQL is syntactically valid and strictly read-only."""
        dialect_name = target_dialect.lower()
        if dialect_name in ("bigquery", "bq"):
            dialect_name = "bigquery"

        try:
            parsed = sqlglot.parse_one(proposed_sql, read=dialect_name)
        except Exception as e:
            return False, f"Proposed repair SQL syntax error: {e}"

        if parsed is None:
            return False, "Proposed repair SQL is empty or invalid."

        for node in parsed.walk():
            if isinstance(node, cls.BLOCKED_NODE_TYPES):
                found_op = node.key.upper()
                msg = f"Proposed repair SQL violates read-only safety policy (found {found_op})."
                return False, msg

        return True, "Proposed repair SQL is syntactically valid and read-only."

    @classmethod
    def validate_target_contract(
        cls,
        original_sql: str,
        proposed_sql: str,
        target_dialect: str,
    ) -> tuple[bool, str]:
        """REPAIR_CONTRACT_CHECK: Verify proposed repair SQL preserves the target contract."""
        dialect_name = target_dialect.lower()
        if dialect_name in ("bigquery", "bq"):
            dialect_name = "bigquery"

        try:
            orig_tree = sqlglot.parse_one(original_sql, read=dialect_name)
            prop_tree = sqlglot.parse_one(proposed_sql, read=dialect_name)
        except Exception as e:
            return False, f"Contract validation failed due to SQL parsing error: {e}"

        if orig_tree is None or prop_tree is None:
            return False, "Contract validation failed: AST could not be generated."

        # Check output column aliases
        orig_aliases = [
            select.alias_or_name.lower()
            for select in orig_tree.selects
            if select.alias_or_name
        ]
        prop_aliases = [
            select.alias_or_name.lower()
            for select in prop_tree.selects
            if select.alias_or_name
        ]

        if orig_aliases and prop_aliases and orig_aliases != prop_aliases:
            return (
                False,
                f"REPAIR_CONTRACT_CHECK VIOLATION: Output column aliases changed from "
                f"{orig_aliases} to {prop_aliases}.",
            )

        # Check referenced tables
        orig_tables = {table.name.lower() for table in orig_tree.find_all(exp.Table) if table.name}
        prop_tables = {table.name.lower() for table in prop_tree.find_all(exp.Table) if table.name}

        if orig_tables != prop_tables:
            return (
                False,
                f"REPAIR_CONTRACT_CHECK VIOLATION: Referenced tables changed from "
                f"{sorted(orig_tables)} to {sorted(prop_tables)}.",
            )

        return True, "REPAIR_CONTRACT_CHECK passed: Target contract preserved."
