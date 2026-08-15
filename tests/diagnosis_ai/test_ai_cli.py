"""Integration tests for Phase 7 CLI tool."""

import subprocess
import sys


def test_cli_diagnose_command():
    cmd = [
        sys.executable,
        "-m",
        "backend.diagnosis_ai.cli",
        "diagnose",
        "--discrepancy-id",
        "D-001",
        "--mock-mode",
        "MOCK_BOUNDARY_REPAIR",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "MIGRA-Q AI DIAGNOSIS" in res.stdout
    assert "Discrepancy ID: D-001" in res.stdout
    assert "REPAIR PROPOSAL" in res.stdout
    assert "Status         : PROPOSED" in res.stdout
    assert "IMPORTANT: Deterministic re-validation required (Phase 8)." in res.stdout

    # Verify absence of forbidden self-approval claims
    assert "REPAIR VERIFIED" not in res.stdout
    assert "MIGRATION FIXED" not in res.stdout
