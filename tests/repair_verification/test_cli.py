"""CLI tests for Phase 8 repair verification entry point."""

import sys
from unittest.mock import patch

import pytest

from backend.repair_verification.cli import main
from backend.repair_verification.models import (
    RepairVerificationResult,
    VerificationMetadata,
    VerificationStatus,
)


def test_cli_help_when_no_args():
    with patch.object(sys, "argv", ["backend.repair_verification.cli"]):
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1


def test_cli_verify_output_formatting(capsys):
    meta = VerificationMetadata(
        verification_id="ver-cli-001",
        repair_id="rep-cli-001",
        discrepancy_id="D-001",
        validation_id_before="val-1",
        execution_id_before="exec-1",
        dataset_id="ds-1",
        dataset_hash_before="dshash",
        validation_config_hash_before="cfghash",
    )
    res = RepairVerificationResult(
        verification_id="ver-cli-001",
        repair_id="rep-cli-001",
        discrepancy_id="D-001",
        validation_id_before="val-1",
        execution_id_before="exec-1",
        status=VerificationStatus.VERIFIED,
        affected_rows_before=10512,
        affected_rows_after=0,
        reduction_percentage=100.0,
        new_discrepancy_count=0,
        remaining_discrepancy_count=0,
        metadata=meta,
        summary="CLI test verified",
    )

    with patch("backend.repair_verification.service.RepairVerificationService.verify_repair", return_value=res):
        with patch.object(sys, "argv", ["cli", "verify", "--repair-id", "rep-cli-001"]):
            main()

    captured = capsys.readouterr().out
    assert "MIGRA-Q REPAIR VERIFICATION" in captured
    assert "10,512" in captured
    assert "100.00%" in captured
    assert "VERIFIED" in captured
    assert "✓ Original discrepancy disappeared" in captured
