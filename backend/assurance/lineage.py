"""Audit lineage builder — validates completeness of the Phase 1–8 artifact chain."""

from __future__ import annotations

from backend.assurance.models import AuditLineage, VerificationPath


class AuditLineageBuilder:
    """Builds and validates the AuditLineage for a migration.

    DIRECT_PASS path: diagnosis/repair/verification artifacts may be absent.
    REPAIRED_PASS path: all artifacts required.
    """

    def build(
        self,
        *,
        path: VerificationPath,
        translation_id: str = "",
        source_execution_id: str = "",
        target_execution_id: str = "",
        validation_id: str = "",
        diagnosis_id: str = "",
        ai_diagnosis_id: str = "",
        repair_id: str = "",
        verification_id: str = "",
    ) -> AuditLineage:
        """Build an AuditLineage and determine its completeness.

        Args:
            path: Explicit VerificationPath determined by assurance logic.
            translation_id: Phase 6 translation ID.
            source_execution_id: Phase 3 source execution ID.
            target_execution_id: Phase 3 target execution ID.
            validation_id: Phase 4 validation ID.
            diagnosis_id: Phase 5 diagnosis ID.
            ai_diagnosis_id: Phase 7 AI diagnosis ID.
            repair_id: Phase 7 repair proposal ID.
            verification_id: Phase 8 verification ID.

        Returns:
            AuditLineage with completeness flag set.
        """

        # Check completeness based on verification path
        has_required = self._check_completeness(
            path=path,
            translation_id=translation_id,
            source_execution_id=source_execution_id,
            target_execution_id=target_execution_id,
            validation_id=validation_id,
            diagnosis_id=diagnosis_id,
            ai_diagnosis_id=ai_diagnosis_id,
            repair_id=repair_id,
            verification_id=verification_id,
        )
        is_complete = has_required and path in (VerificationPath.DIRECT_PASS, VerificationPath.REPAIRED_PASS)

        return AuditLineage(
            translation_id=translation_id,
            source_execution_id=source_execution_id,
            target_execution_id=target_execution_id,
            validation_id=validation_id,
            diagnosis_id=diagnosis_id,
            ai_diagnosis_id=ai_diagnosis_id,
            repair_id=repair_id,
            verification_id=verification_id,
            verification_path=path,
            is_complete=is_complete,
        )

    def get_missing_fields(
        self,
        lineage: AuditLineage,
    ) -> list[str]:
        """Return a list of missing field names for the lineage's verification path."""
        missing: list[str] = []
        required = self._get_required_fields(lineage.verification_path)
        data = lineage.model_dump()
        for field in required:
            if not data.get(field):
                missing.append(field)
        return missing

    def _check_completeness(
        self,
        *,
        path: VerificationPath,
        translation_id: str,
        source_execution_id: str,
        target_execution_id: str,
        validation_id: str,
        diagnosis_id: str,
        ai_diagnosis_id: str,
        repair_id: str,
        verification_id: str,
    ) -> bool:
        """Check whether all required fields for the given path are non-empty."""
        values = {
            "translation_id": translation_id,
            "source_execution_id": source_execution_id,
            "target_execution_id": target_execution_id,
            "validation_id": validation_id,
            "diagnosis_id": diagnosis_id,
            "ai_diagnosis_id": ai_diagnosis_id,
            "repair_id": repair_id,
            "verification_id": verification_id,
        }
        required = self._get_required_fields(path)
        return all(bool(values.get(f)) for f in required)

    @staticmethod
    def _get_required_fields(path: VerificationPath) -> list[str]:
        """Return the list of required lineage fields for the given path."""
        base = [
            "translation_id",
            "source_execution_id",
            "target_execution_id",
            "validation_id",
        ]
        if path == VerificationPath.REPAIRED_PASS:
            return base + [
                "diagnosis_id",
                "ai_diagnosis_id",
                "repair_id",
                "verification_id",
            ]
        elif path == VerificationPath.REPAIR_FAILED:
            return base + [
                "diagnosis_id",
                "ai_diagnosis_id",
                "repair_id",
            ]
        elif path == VerificationPath.REPAIR_NOT_EXECUTED:
            return base
        return base
