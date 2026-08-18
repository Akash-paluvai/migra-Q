"""Tests for Phase 9 audit lineage builder."""

import pytest

from backend.assurance.lineage import AuditLineageBuilder
from backend.assurance.models import VerificationPath


@pytest.fixture
def builder():
    return AuditLineageBuilder()


class TestDirectPassLineage:
    def test_complete_direct_pass(self, builder):
        lineage = builder.build(
            translation_id="TRN-001",
            source_execution_id="EXEC-SRC",
            target_execution_id="EXEC-TGT",
            validation_id="VAL-001",
            path=VerificationPath.DIRECT_PASS,
        )
        assert lineage.verification_path == VerificationPath.DIRECT_PASS
        assert lineage.is_complete is True

    def test_direct_pass_missing_translation(self, builder):
        lineage = builder.build(
            translation_id="",
            source_execution_id="EXEC-SRC",
            target_execution_id="EXEC-TGT",
            validation_id="VAL-001",
            path=VerificationPath.DIRECT_PASS,
        )
        assert lineage.is_complete is False

    def test_direct_pass_does_not_require_repair_artifacts(self, builder):
        lineage = builder.build(
            translation_id="TRN-001",
            source_execution_id="EXEC-SRC",
            target_execution_id="EXEC-TGT",
            validation_id="VAL-001",
            diagnosis_id="",
            ai_diagnosis_id="",
            repair_id="",
            verification_id="",
            path=VerificationPath.DIRECT_PASS,
        )
        assert lineage.is_complete is True


class TestRepairedPassLineage:
    def test_complete_repaired_pass(self, builder):
        lineage = builder.build(
            translation_id="TRN-001",
            source_execution_id="EXEC-SRC",
            target_execution_id="EXEC-TGT",
            validation_id="VAL-001",
            diagnosis_id="DIAG-001",
            ai_diagnosis_id="AIDIAG-001",
            repair_id="REP-001",
            verification_id="VER-001",
            path=VerificationPath.REPAIRED_PASS,
        )
        assert lineage.verification_path == VerificationPath.REPAIRED_PASS
        assert lineage.is_complete is True

    def test_repaired_pass_missing_repair_id(self, builder):
        lineage = builder.build(
            translation_id="TRN-001",
            source_execution_id="EXEC-SRC",
            target_execution_id="EXEC-TGT",
            validation_id="VAL-001",
            diagnosis_id="DIAG-001",
            ai_diagnosis_id="AIDIAG-001",
            repair_id="",
            verification_id="VER-001",
            path=VerificationPath.REPAIRED_PASS,
        )
        assert lineage.is_complete is False

    def test_repaired_pass_missing_verification(self, builder):
        lineage = builder.build(
            translation_id="TRN-001",
            source_execution_id="EXEC-SRC",
            target_execution_id="EXEC-TGT",
            validation_id="VAL-001",
            diagnosis_id="DIAG-001",
            ai_diagnosis_id="AIDIAG-001",
            repair_id="REP-001",
            verification_id="",
            path=VerificationPath.REPAIRED_PASS,
        )
        assert lineage.is_complete is False


class TestMissingFields:
    def test_get_missing_fields_direct_pass(self, builder):
        lineage = builder.build(
            translation_id="TRN-001",
            source_execution_id="",
            target_execution_id="EXEC-TGT",
            validation_id="",
            path=VerificationPath.DIRECT_PASS,
        )
        missing = builder.get_missing_fields(lineage)
        assert "source_execution_id" in missing
        assert "validation_id" in missing
        assert "repair_id" not in missing

    def test_get_missing_fields_repaired_pass(self, builder):
        lineage = builder.build(
            translation_id="TRN-001",
            source_execution_id="EXEC-SRC",
            target_execution_id="EXEC-TGT",
            validation_id="VAL-001",
            diagnosis_id="",
            ai_diagnosis_id="",
            repair_id="",
            verification_id="",
            path=VerificationPath.REPAIRED_PASS,
        )
        missing = builder.get_missing_fields(lineage)
        assert "diagnosis_id" in missing
        assert "ai_diagnosis_id" in missing
        assert "repair_id" in missing
        assert "verification_id" in missing
