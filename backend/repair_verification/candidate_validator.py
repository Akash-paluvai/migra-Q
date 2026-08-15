"""CandidateRepairValidator — 12 pre-execution integrity checks for Phase 8 repair proposals."""

from __future__ import annotations

import sqlglot
from sqlglot import exp

from backend.diagnosis_ai.models import RepairProposal, RepairStatus
from backend.diagnosis_ai.scope import RepairScopeChecker
from backend.diagnosis_ai.validator import RepairProposalValidator


class CandidateRepairValidator:
    """Validator executing 12 pre-execution integrity checks on a RepairProposal before DuckDB execution."""

    @classmethod
    def validate_candidate(
        cls,
        proposal: RepairProposal,
        original_target_sql: str,
        target_dialect: str = "bigquery",
        expected_tables: list[str] | None = None,
        stored_proposal_sql: str | None = None,
    ) -> tuple[bool, str, dict]:
        """Run 12 candidate integrity checks before execution.

        Returns (is_valid, rejection_reason, details_dict).
        """
        # 1. Status check: must be PROPOSED
        if proposal.status != RepairStatus.PROPOSED:
            return False, "STATUS_NOT_PROPOSED", {"status": proposal.status.value}

        # 2. Non-empty proposed SQL
        proposed_sql = proposal.proposed_sql.strip() if proposal.proposed_sql else ""
        if not proposed_sql:
            return False, "EMPTY_PROPOSED_SQL", {}

        # 3. Original target SQL availability
        orig_sql = original_target_sql.strip() if original_target_sql else ""
        if not orig_sql:
            return False, "MISSING_ORIGINAL_TARGET_SQL", {}

        # 4. Unchanged repair check (proposed SQL must not be identical to original target SQL)
        if orig_sql.rstrip(";").strip() == proposed_sql.rstrip(";").strip():
            return False, "UNCHANGED_REPAIR_SQL", {"original_sql": orig_sql, "proposed_sql": proposed_sql}

        # 5. Stored proposal artifact mismatch check
        if stored_proposal_sql is not None:
            stored_sql_clean = stored_proposal_sql.strip().rstrip(";").strip()
            if stored_sql_clean != proposed_sql.rstrip(";").strip():
                return False, "REPAIR_ARTIFACT_MISMATCH", {
                    "stored_sql": stored_proposal_sql,
                    "proposed_sql": proposed_sql,
                }

        # 6. Syntax check (SQLGlot parse)
        dialect_name = target_dialect.lower()
        if dialect_name in ("bigquery", "bq"):
            dialect_name = "bigquery"

        try:
            parsed = sqlglot.parse_one(proposed_sql, read=dialect_name)
        except Exception as e:
            return False, "SQL_SYNTAX_ERROR", {"error": str(e)}

        if parsed is None:
            return False, "SQL_SYNTAX_ERROR", {"error": "AST could not be generated"}

        # 7. Read-only safety check (no mutation AST nodes)
        valid_syntax, safety_msg = RepairProposalValidator.validate_repair_syntax_and_safety(
            proposed_sql, target_dialect
        )
        if not valid_syntax:
            return False, "READ_ONLY_VIOLATION", {"details": safety_msg}

        # 8. Target schema consistency check (must contain valid query structure)
        if not (isinstance(parsed, exp.Select) or parsed.find(exp.Select)):
            return False, "SCHEMA_INCONSISTENCY", {"reason": "Proposed SQL does not contain a SELECT query"}

        # 9. Known discrepancy mapping
        if not proposal.discrepancy_id:
            return False, "UNKNOWN_DISCREPANCY_MAPPING", {}

        # 10. Required dataset tables referenced check
        if expected_tables:
            parsed_tables = [t.name.lower() for t in parsed.find_all(exp.Table)]
            for tbl in expected_tables:
                if tbl.lower() not in parsed_tables and not any(tbl.lower() in p for p in parsed_tables):
                    return False, "MISSING_REQUIRED_TABLE", {"missing_table": tbl, "found_tables": parsed_tables}

        # 11. Target contract preservation check (column aliases)
        valid_contract, contract_msg = RepairProposalValidator.validate_target_contract(
            orig_sql, proposed_sql, target_dialect
        )
        if not valid_contract:
            return False, "CONTRACT_ALIAS_MISMATCH", {"details": contract_msg}

        # 12. AST Scope constraint check (Phase 7 RepairScopeChecker)
        valid_scope, scope_msg, constraints = RepairScopeChecker.verify_repair_scope(
            orig_sql, proposed_sql, target_dialect, proposal.changed_region or "columns"
        )
        if not valid_scope:
            return False, "SCOPE_CONSTRAINT_VIOLATION", {"details": scope_msg, "constraints_checked": constraints}

        return True, "CANDIDATE_ACCEPTED", {
            "checks_passed": 12,
            "constraints_checked": constraints,
        }
