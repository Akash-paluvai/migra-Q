"""Centralized Artifact State & Lifecycle Consistency Validator.

Enforces strict lifecycle consistency rules across all pipeline artifacts.
Prevents contradictory state combinations, synthetic successes, and illegal phase skips.
"""

from __future__ import annotations

from typing import Any


class ArtifactStateConsistencyError(ValueError):
    """Raised when an artifact state combination violates lifecycle consistency invariants."""
    pass


class ArtifactStateConsistencyValidator:
    """Validator enforcing lifecycle and artifact consistency invariants."""

    @classmethod
    def validate_translation_state(
        cls,
        status: str,
        target_sql: str | None,
        candidate_validation_status: str | None,
    ) -> None:
        """Validate Phase 6 Translation artifact consistency."""
        status_upper = (status or "").upper()
        cand_val_upper = (candidate_validation_status or "").upper() if candidate_validation_status else None

        if status_upper != "SUCCESS":
            if cand_val_upper == "VALID_SYNTAX":
                raise ArtifactStateConsistencyError(
                    f"IMPOSSIBLE_STATE: Translation status is '{status}' but candidate_validation_status is 'VALID_SYNTAX'. "
                    f"Failed translations cannot have VALID_SYNTAX."
                )
            if target_sql and target_sql.strip():
                raise ArtifactStateConsistencyError(
                    f"IMPOSSIBLE_STATE: Translation status is '{status}' but non-empty target_sql is present. "
                    f"Failed translations must not produce target SQL."
                )

    @classmethod
    def validate_execution_state(
        cls,
        target_sql: str | None,
        target_execution_status: str | None,
    ) -> None:
        """Validate Phase 3 Execution artifact consistency."""
        if not target_sql or not target_sql.strip():
            if target_execution_status and target_execution_status.upper() == "SUCCESS":
                raise ArtifactStateConsistencyError(
                    "IMPOSSIBLE_STATE: target_sql is missing/empty but target_execution status is 'SUCCESS'."
                )

    @classmethod
    def validate_validation_state(
        cls,
        target_execution_status: str | None,
        validation_status: str | None,
    ) -> None:
        """Validate Phase 4 Validation artifact consistency."""
        tgt_status = (target_execution_status or "").upper()
        val_status = (validation_status or "").upper()

        if tgt_status != "SUCCESS" and val_status in ("PASS", "FAIL", "WARN"):
            raise ArtifactStateConsistencyError(
                f"IMPOSSIBLE_STATE: target_execution status is '{target_execution_status}' but validation status is '{validation_status}'. "
                f"Validation cannot evaluate without successful execution."
            )

    @classmethod
    def validate_repair_state(
        cls,
        repair_id: str | None,
        repair_status: str | None,
        proposed_sql: str | None,
    ) -> None:
        """Validate Phase 7/8 Repair proposal consistency."""
        rep_status = (repair_status or "").upper()
        if not repair_id or not repair_id.strip():
            if rep_status in ("PROPOSED", "VERIFIED"):
                raise ArtifactStateConsistencyError(
                    f"IMPOSSIBLE_STATE: repair_id is None/empty but repair status is '{repair_status}'."
                )
        if not proposed_sql or not proposed_sql.strip():
            if rep_status == "VERIFIED":
                raise ArtifactStateConsistencyError(
                    "IMPOSSIBLE_STATE: proposed_sql is None/empty but repair status is 'VERIFIED'."
                )

    @classmethod
    def validate_verification_state(
        cls,
        verification_id: str | None,
        verification_status: str | None,
    ) -> None:
        """Validate Phase 8 Verification artifact consistency."""
        ver_status = (verification_status or "").upper()
        if not verification_id or not verification_id.strip():
            if ver_status == "VERIFIED":
                raise ArtifactStateConsistencyError(
                    f"IMPOSSIBLE_STATE: verification_id is None/empty but verification status is '{verification_status}'."
                )

    @classmethod
    def validate_assurance_state(
        cls,
        final_status: str,
        evidence_score: float | None,
        validation_ran: bool,
    ) -> None:
        """Validate Phase 9 Assurance report consistency."""
        final_upper = (final_status or "").upper()

        if not validation_ran:
            if evidence_score is not None:
                raise ArtifactStateConsistencyError(
                    f"IMPOSSIBLE_STATE: Validation did not run, but assurance evidence_score is {evidence_score}. "
                    f"Score must be None when validation evidence does not exist."
                )
            if final_upper == "VERIFIED":
                raise ArtifactStateConsistencyError(
                    "IMPOSSIBLE_STATE: Validation did not run, but final_status is 'VERIFIED'."
                )
        else:
            if final_upper == "VERIFIED" and evidence_score is None:
                raise ArtifactStateConsistencyError(
                    "IMPOSSIBLE_STATE: final_status is 'VERIFIED' but evidence_score is None."
                )

    @classmethod
    def validate_full_pipeline_state(
        cls,
        *,
        translation_status: str,
        target_sql: str | None,
        candidate_validation_status: str | None,
        target_execution_status: str | None,
        validation_status: str | None,
        validation_ran: bool,
        repair_id: str | None,
        repair_status: str | None,
        proposed_sql: str | None,
        verification_id: str | None,
        verification_status: str | None,
        final_status: str,
        evidence_score: float | None,
    ) -> None:
        """Validate comprehensive state consistency across all pipeline phases."""
        cls.validate_translation_state(translation_status, target_sql, candidate_validation_status)
        cls.validate_execution_state(target_sql, target_execution_status)
        cls.validate_validation_state(target_execution_status, validation_status)
        cls.validate_repair_state(repair_id, repair_status, proposed_sql)
        cls.validate_verification_state(verification_id, verification_status)
        cls.validate_assurance_state(final_status, evidence_score, validation_ran)
