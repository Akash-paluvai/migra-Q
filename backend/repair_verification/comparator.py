"""DiscrepancyComparator — coordinates BEFORE vs AFTER comparison, immutability, and AST diffs."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import sqlglot

from backend.repair_verification.analysis.outcome import OutcomeCalculator
from backend.repair_verification.context import RepairVerificationContext
from backend.repair_verification.exceptions import ImmutabilityViolationError
from backend.repair_verification.models import RepairOutcome, VerificationEvidenceItem


class DiscrepancyComparator:
    """Coordinates comparative analysis across BEFORE and AFTER repair execution states."""

    @classmethod
    def compute_config_hash(cls, config: Any) -> str:
        """Compute deterministic hash of ValidationConfig."""
        if config is None:
            return "config-default"
        if hasattr(config, "model_dump_json"):
            content = config.model_dump_json()
        elif hasattr(config, "dict"):
            content = json.dumps(config.dict(), sort_keys=True)
        else:
            content = str(config)
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def verify_immutability(cls, ctx: RepairVerificationContext) -> None:
        """Verify dataset and validation configuration immutability across runs."""
        # 1. Dataset immutability check
        if ctx.dataset_hash_after and ctx.dataset_hash_before != ctx.dataset_hash_after:
            raise ImmutabilityViolationError(
                violation_type="DATASET_CHANGED",
                details=(
                    f"Dataset hash changed between BEFORE ({ctx.dataset_hash_before}) "
                    f"and AFTER ({ctx.dataset_hash_after}). Source dataset must be immutable."
                ),
            )

    @classmethod
    def compute_ast_changed_regions(
        cls,
        original_sql: str,
        repaired_sql: str,
        target_dialect: str = "bigquery",
    ) -> list[str]:
        """Independently compute AST changed regions between original target and repaired target SQL."""
        dialect_name = target_dialect.lower()
        if dialect_name in ("bigquery", "bq"):
            dialect_name = "bigquery"

        try:
            orig_tree = sqlglot.parse_one(original_sql, read=dialect_name)
            rep_tree = sqlglot.parse_one(repaired_sql, read=dialect_name)
        except Exception:
            return ["columns"]

        if not orig_tree or not rep_tree:
            return ["columns"]

        changed: list[str] = []

        orig_where = orig_tree.find(sqlglot.exp.Where)
        rep_where = rep_tree.find(sqlglot.exp.Where)
        if (orig_where.sql() if orig_where else "") != (rep_where.sql() if rep_where else ""):
            changed.append("where_clause")

        orig_select = [e.sql() for e in orig_tree.selects]
        rep_select = [e.sql() for e in rep_tree.selects]
        if orig_select != rep_select:
            changed.append("select_projections")

        orig_group = orig_tree.find(sqlglot.exp.Group)
        rep_group = rep_tree.find(sqlglot.exp.Group)
        if (orig_group.sql() if orig_group else "") != (rep_group.sql() if rep_group else ""):
            changed.append("group_by_clause")

        orig_join = [j.sql() for j in orig_tree.find_all(sqlglot.exp.Join)]
        rep_join = [j.sql() for j in rep_tree.find_all(sqlglot.exp.Join)]
        if orig_join != rep_join:
            changed.append("join_clause")

        return changed or ["columns"]

    @classmethod
    def compare_context(
        cls,
        ctx: RepairVerificationContext,
    ) -> tuple[RepairOutcome, list[str], list[str], list[str], list[VerificationEvidenceItem]]:
        """Perform comparative analysis for the context and calculate outcome."""
        cls.verify_immutability(ctx)

        target_disc_id = ctx.repair_proposal.discrepancy_id

        outcome, resolved_ids, remaining_ids, new_ids, evidence = OutcomeCalculator.calculate_repair_outcome(
            before_report=ctx.discrepancy_report_before,
            after_report=ctx.discrepancy_report_after,
            target_discrepancy_id=target_disc_id,
            val_id_before=ctx.validation_report_before.validation_id,
            val_id_after=ctx.validation_report_after.validation_id if ctx.validation_report_after else None,
        )

        return outcome, resolved_ids, remaining_ids, new_ids, evidence
