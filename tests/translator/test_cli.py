"""Unit tests for Phase 6 Translation CLI."""

import subprocess
import sys


def test_cli_translate_help():
    cmd = [sys.executable, "-m", "backend.translator.cli", "translate", "--help"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "--source-dialect" in res.stdout
    assert "--target-dialect" in res.stdout


def test_cli_translate_flagship_file():
    cmd = [
        sys.executable,
        "-m",
        "backend.translator.cli",
        "translate",
        "--input",
        "examples/translation/customer_risk.sql",
        "--source-dialect",
        "teradata",
        "--target-dialect",
        "bigquery",
        "--provider",
        "mock",
        "--mock-mode",
        "MOCK_GOOD",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0
    assert "MIGRA-Q TRANSLATION" in res.stdout
    assert "Status        : SUCCESS" in res.stdout
    assert "Candidate Check: VALID_SYNTAX" in res.stdout
    assert "Target Candidate SQL:" in res.stdout
    assert "Candidate SQL syntactically valid" in res.stdout

    # CRITICAL: Verify CLI NEVER outputs "migration verified", "equivalent", "safe", or "approved"!
    low_out = res.stdout.lower()
    assert "migration verified" not in low_out
    assert "equivalent" not in low_out
    assert "approved" not in low_out
