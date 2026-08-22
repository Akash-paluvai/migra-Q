"""Schema Preflight Validator.

Deterministically validates source SQL against the dataset schema before execution.
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

from backend.assurance.models import MissingColumnRef, PreflightSummary
from backend.core.logging import get_logger
from backend.datasets.registry import DatasetRegistry

logger = get_logger(__name__)


class SchemaPreflightValidator:
    """Validates SQL table and column references against the target dataset schema."""

    @classmethod
    def validate(cls, sql: str, dataset_id: str, dialect: str = "teradata") -> PreflightSummary:
        """Parse SQL and ensure all referenced tables and columns exist in the dataset."""
        try:
            parsed = sqlglot.parse_one(sql, read=dialect.lower())
        except Exception as e:
            # If we can't parse it, we can't do preflight. We'll let it fail at execution.
            logger.warning(f"Schema preflight skipped due to parse error: {e}")
            return PreflightSummary(status="PASS", execution_allowed=True)

        registry = DatasetRegistry()
        dataset = registry.get_dataset(dataset_id)
        if not dataset:
            return PreflightSummary(
                status="FAILED",
                failure_category="DATASET_NOT_FOUND",
                execution_allowed=False,
                reason=f"Dataset '{dataset_id}' not found.",
            )

        # Build schema map
        schema_map: dict[str, list[str]] = {}
        for t_summary in dataset.table_summaries:
            t_name = t_summary.table_name.lower()
            schema_map[t_name] = [c.name.lower() for c in t_summary.columns]

        # Extract CTE names so we don't flag them as missing tables
        ctes = set()
        for with_ in parsed.find_all(exp.With):
            for cte in with_.expressions:
                ctes.add(cte.alias.lower())

        # Extract table aliases
        aliases: dict[str, str] = {}
        for table in parsed.find_all(exp.Table):
            t_name_lower = table.name.lower()
            if t_name_lower in ctes:
                continue
            if table.alias:
                aliases[table.alias.lower()] = t_name_lower
            else:
                aliases[t_name_lower] = t_name_lower

        # Check for unresolved tables
        unresolved_tables = []
        for t_name in set(aliases.values()):
            if t_name and t_name not in schema_map:
                unresolved_tables.append(t_name)

        if unresolved_tables:
            return PreflightSummary(
                status="FAILED",
                failure_category="INPUT_SCHEMA_MISMATCH",
                execution_allowed=False,
                unresolved_tables=unresolved_tables,
                reason="The SQL could not be executed because it references tables that do not exist in the selected dataset.",
                available_columns=schema_map
            )

        missing_columns: list[MissingColumnRef] = []
        for col in parsed.find_all(exp.Column):
            # Ignore function arguments that look like columns if they're actually keywords (e.g. EXTRACT(DAY FROM x))
            if not col.name or col.name.upper() in ("YEAR", "MONTH", "DAY", "HOUR", "MINUTE", "SECOND"):
                if isinstance(col.parent, exp.Extract) or isinstance(col.parent, exp.CurrentDate) or isinstance(col.parent, exp.CurrentTimestamp):
                    continue
            
            c_name = col.name.lower()
            t_alias = col.table.lower() if col.table else None
            
            if t_alias:
                if t_alias in ctes:
                    continue # Column from a CTE
                t_name = aliases.get(t_alias)
                if not t_name:
                    continue
                if t_name in schema_map:
                    if c_name not in schema_map[t_name]:
                        missing_columns.append(MissingColumnRef(table=t_name, column=col.name))
            else:
                # Unqualified column. Does it exist in ANY of the referenced tables?
                found = False
                for t_name in set(aliases.values()):
                    if t_name in schema_map and c_name in schema_map[t_name]:
                        found = True
                        break
                if not found:
                    missing_columns.append(MissingColumnRef(table=None, column=col.name))

        if missing_columns:
            # Gather available columns for context
            context_tables = set(ref.table for ref in missing_columns if ref.table)
            if not context_tables:
                context_tables = set(aliases.values())
            
            available_cols = {t: schema_map[t] for t in context_tables if t in schema_map}

            # Deduplicate missing columns
            dedup_missing = []
            seen = set()
            for mc in missing_columns:
                k = f"{mc.table}.{mc.column}"
                if k not in seen:
                    seen.add(k)
                    dedup_missing.append(mc)

            return PreflightSummary(
                status="FAILED",
                failure_category="INPUT_SCHEMA_MISMATCH",
                execution_allowed=False,
                missing_columns=dedup_missing,
                available_columns=available_cols,
                reason="The SQL could not be executed against the selected dataset because it references columns that do not exist in the dataset."
            )

        return PreflightSummary(status="PASS", execution_allowed=True)
