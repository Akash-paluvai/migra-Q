"""Test the semantic confidence contract across all classification categories.

Tests the complete architecture:
  SQLGlot → Compatibility Analysis (with confidence) → DuckDB → Classifier

Category matrix:
  A   Generic SQL               → SUCCESS, EXACT
  B   ZEROIFNULL adapter        → SUCCESS, EXACT
  B2  NULLIFZERO adapter        → SUCCESS, EXACT
  C   Unknown function          → UNSUPPORTED_CAPABILITY
  D   Missing column            → EXECUTION_ERROR
  E   Standard func bad sig     → EXECUTION_ERROR, SANDBOX_FUNCTION_SIGNATURE_MISMATCH
  E2  Dialect validation helper → direct unit tests
  F   Confidence aggregation    → EXACT < SAFE_EQUIVALENT < APPROXIMATION < UNKNOWN
"""
import sys
import json
from pathlib import Path

from backend.execution.duckdb_runner import run_duckdb_execution, _is_function_dialect_specific
from backend.execution.models import ExecutionRequest
from backend.execution.dataset_loader import ResolvedDataset
from backend.execution.dialect_transforms.base import (
    SemanticConfidence,
    CompatibilityResult,
    CompatibilityAnalysis,
)
from backend.execution.dialect_transforms import analyze_and_transform

DATASET_DIR = Path("/Users/akashpaluvai/college/migraq/datasets/generated/join_semantics")


def make_dataset():
    manifest = json.loads((DATASET_DIR / "manifest.json").read_text())
    return ResolvedDataset(
        dataset_id="join_semantics",
        dataset_dir=DATASET_DIR,
        manifest=manifest,
        dataset_hash="test",
    )


def run_test(name, sql, dialect="teradata", expected_status=None, expected_code=None, expected_confidence=None):
    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"{'='*70}")
    print(f"  SQL:      {sql}")
    print(f"  Dialect:  {dialect}")

    req = ExecutionRequest(sql=sql, dialect=dialect, dataset_id="join_semantics")
    res = run_duckdb_execution(req, make_dataset())

    status = res.status.value
    code = res.error_code
    confidence = res.compatibility_confidence

    print(f"  Status:     {status}")
    print(f"  Code:       {code}")
    print(f"  Confidence: {confidence}")

    if res.error_message and res.error_message.startswith("{"):
        try:
            err = json.loads(res.error_message)
            print(f"  Function:   {err.get('function', 'N/A')}")
        except json.JSONDecodeError:
            pass

    passed = True
    if expected_status and status != expected_status:
        print(f"  ✗ EXPECTED status={expected_status}, GOT status={status}")
        passed = False
    if expected_code and code != expected_code:
        print(f"  ✗ EXPECTED code={expected_code}, GOT code={code}")
        passed = False
    if expected_confidence and confidence != expected_confidence:
        print(f"  ✗ EXPECTED confidence={expected_confidence}, GOT confidence={confidence}")
        passed = False
    if passed:
        print(f"  ✓ PASS")
    return passed


if __name__ == "__main__":
    if not DATASET_DIR.exists():
        print(f"Dataset dir not found: {DATASET_DIR}")
        sys.exit(1)

    results = []

    # ── Execution tests ───────────────────────────────────────────
    results.append(run_test(
        "A  Generic SQL",
        "SELECT 1 AS val",
        expected_status="SUCCESS",
        expected_confidence="EXACT",
    ))

    results.append(run_test(
        "B  ZEROIFNULL adapter (EXACT)",
        "SELECT ZEROIFNULL(123) AS val",
        expected_status="SUCCESS",
        expected_confidence="EXACT",
    ))

    results.append(run_test(
        "B2 NULLIFZERO adapter (EXACT)",
        "SELECT NULLIFZERO(0) AS val",
        expected_status="SUCCESS",
        expected_confidence="EXACT",
    ))

    results.append(run_test(
        "C  Unknown proprietary function",
        "SELECT SOME_COMPLETELY_UNKNOWN_FUNCTION(123) AS val",
        expected_status="UNSUPPORTED_CAPABILITY",
        expected_code="SANDBOX_UNSUPPORTED_FUNCTION",
    ))

    results.append(run_test(
        "D  Missing column (EXECUTION_ERROR)",
        "SELECT nonexistent_column",
        expected_status="EXECUTION_ERROR",
    ))

    results.append(run_test(
        "E  Signature mismatch - standard func",
        "SELECT substr('a')",
        expected_status="EXECUTION_ERROR",
        expected_code="SANDBOX_FUNCTION_SIGNATURE_MISMATCH",
    ))

    # ── Dialect validation helper ─────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  E2 Dialect validation helper")
    print(f"{'='*70}")

    r1 = _is_function_dialect_specific("SELECT substr('a')", "teradata", "substring")
    print(f"  substr → dialect_specific={r1} (expected: False)")
    assert not r1

    r2 = _is_function_dialect_specific("SELECT ZEROIFNULL(123)", "teradata", "zeroifnull")
    print(f"  ZEROIFNULL → dialect_specific={r2} (expected: True)")
    assert r2

    r3 = _is_function_dialect_specific("SELECT SOME_UNKNOWN_FUNC(1,2)", "teradata", "some_unknown_func")
    print(f"  SOME_UNKNOWN_FUNC → dialect_specific={r3} (expected: True)")
    assert r3

    print(f"  ✓ PASS")
    results.append(True)

    # ── Confidence ordering / aggregation ─────────────────────────
    print(f"\n{'='*70}")
    print(f"  F  SemanticConfidence ordering and aggregation")
    print(f"{'='*70}")

    assert SemanticConfidence.EXACT < SemanticConfidence.SAFE_EQUIVALENT
    assert SemanticConfidence.SAFE_EQUIVALENT < SemanticConfidence.APPROXIMATION
    assert SemanticConfidence.APPROXIMATION < SemanticConfidence.UNKNOWN
    assert not (SemanticConfidence.UNKNOWN < SemanticConfidence.EXACT)
    print(f"  Ordering: EXACT < SAFE_EQUIVALENT < APPROXIMATION < UNKNOWN ✓")

    # Aggregate: max of [EXACT, EXACT] = EXACT
    confs = [SemanticConfidence.EXACT, SemanticConfidence.EXACT]
    assert max(confs) == SemanticConfidence.EXACT
    print(f"  max([EXACT, EXACT]) = EXACT ✓")

    # Aggregate: max of [EXACT, SAFE_EQUIVALENT] = SAFE_EQUIVALENT
    confs2 = [SemanticConfidence.EXACT, SemanticConfidence.SAFE_EQUIVALENT]
    assert max(confs2) == SemanticConfidence.SAFE_EQUIVALENT
    print(f"  max([EXACT, SAFE_EQUIVALENT]) = SAFE_EQUIVALENT ✓")

    # Aggregate: max of [EXACT, APPROXIMATION] = APPROXIMATION
    confs3 = [SemanticConfidence.EXACT, SemanticConfidence.APPROXIMATION]
    assert max(confs3) == SemanticConfidence.APPROXIMATION
    print(f"  max([EXACT, APPROXIMATION]) = APPROXIMATION ✓")

    print(f"  ✓ PASS")
    results.append(True)

    # ── Analyze and transform ─────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  G  analyze_and_transform returns CompatibilityAnalysis")
    print(f"{'='*70}")

    import sqlglot
    parsed = sqlglot.parse_one("SELECT ZEROIFNULL(123) AS val", read="teradata")
    analysis = analyze_and_transform(parsed, "teradata")

    assert isinstance(analysis, CompatibilityAnalysis)
    assert analysis.executable is True
    assert analysis.aggregate_confidence == SemanticConfidence.EXACT
    print(f"  ZEROIFNULL → executable={analysis.executable}, confidence={analysis.aggregate_confidence.value} ✓")

    parsed2 = sqlglot.parse_one("SELECT 1 AS val", read="teradata")
    analysis2 = analyze_and_transform(parsed2, "teradata")
    assert analysis2.aggregate_confidence == SemanticConfidence.EXACT
    print(f"  Generic SQL → confidence={analysis2.aggregate_confidence.value} ✓")

    print(f"  ✓ PASS")
    results.append(True)

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    total = len(results)
    passed = sum(1 for r in results if r)
    print(f"  RESULTS: {passed}/{total} passed")
    print(f"{'='*70}")

    sys.exit(0 if all(results) else 1)
