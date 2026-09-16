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
from backend.execution.models import ExecutionRequest, ExecutionMode
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


def run_test(name, sql, dialect="teradata", expected_status=None, expected_code=None, expected_confidence=None, execution_mode=ExecutionMode.SOURCE, claimed_target_constructs=None):
    print(f"\n{'='*70}")
    print(f"  {name}")
    print(f"{'='*70}")
    print(f"  SQL:      {sql}")
    print(f"  Dialect:  {dialect}")
    print(f"  Mode:     {execution_mode.name}")

    req = ExecutionRequest(
        sql=sql, 
        dialect=dialect, 
        dataset_id="join_semantics",
        execution_mode=execution_mode,
        claimed_target_constructs=claimed_target_constructs or []
    )
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
        except json.DecodeError:
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
        "C  Unknown proprietary function (Target Capability Unsupported)",
        "SELECT SOME_COMPLETELY_UNKNOWN_FUNCTION(123) AS val",
        dialect="bigquery",
        execution_mode=ExecutionMode.TARGET,
        claimed_target_constructs=[],
        expected_status="TARGET_CAPABILITY_UNSUPPORTED",
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

    # ── Target Capability vs Sandbox Limitation Boundaries ────────
    print(f"\n{'='*70}")
    print(f"  H  Assurance Service Boundary Proofs")
    print(f"{'='*70}")

    from backend.assurance.service import MigrationAssuranceService
    from backend.execution.models import ExecutionRequest, ExecutionResult, ExecutionStatus, ExecutionMode
    from backend.validation.models import ValidationReport
    from backend.translator.models import TranslationResult, TranslationResponse, CandidateValidationStatus, TranslationMetadata
    from backend.translator.models import TranslationStatus

    def dummy_exec(status, conf="EXACT"):
        return ExecutionResult(
            execution_id="dummy", query_hash="dummy", dataset_id="dummy", dataset_hash="dummy",
            status=status, compatibility_confidence=conf
        )

    # Test A: BigQuery + FARM_FINGERPRINT -> TARGET SUPPORTED -> SANDBOX_LIMITATION -> INCONCLUSIVE
    # duckdb_runner test:
    req_a = ExecutionRequest(
        sql="SELECT FARM_FINGERPRINT('test')", 
        dialect="bigquery", 
        dataset_id="join_semantics", 
        execution_mode=ExecutionMode.TARGET,
        claimed_target_constructs=["FARM_FINGERPRINT"]
    )
    res_a = run_duckdb_execution(req_a, make_dataset())
    assert res_a.status == ExecutionStatus.SANDBOX_LIMITATION
    print("  Test A (Runner): Valid target function fails in Sandbox -> SANDBOX_LIMITATION ✓")
    
    # Assurance test for Test A:
    service = MigrationAssuranceService()
    src_a = dummy_exec(ExecutionStatus.SUCCESS)
    tgt_a = dummy_exec(ExecutionStatus.SANDBOX_LIMITATION)
    report_a = service.evaluate_assurance(
        migration_id="dummy_a",
        source_execution=src_a, 
        target_execution=tgt_a
    )
    assert report_a.final_status.name == "INCONCLUSIVE"
    assert "DuckDB sandbox cannot execute" in report_a.decision_reason
    print("  Test A (Assurance): SANDBOX_LIMITATION -> INCONCLUSIVE ✓")

    # Test B: Deliberately invalid target function -> TARGET_CAPABILITY_UNSUPPORTED
    req_b = ExecutionRequest(
        sql="SELECT FAKE_BQ_FUNC('test')", 
        dialect="bigquery", 
        dataset_id="join_semantics", 
        execution_mode=ExecutionMode.TARGET,
        claimed_target_constructs=[]
    )
    res_b = run_duckdb_execution(req_b, make_dataset())
    assert res_b.status == ExecutionStatus.TARGET_CAPABILITY_UNSUPPORTED
    print("  Test B (Runner): Invalid target function -> TARGET_CAPABILITY_UNSUPPORTED ✓")
    
    src_b = dummy_exec(ExecutionStatus.SUCCESS)
    tgt_b = dummy_exec(ExecutionStatus.TARGET_CAPABILITY_UNSUPPORTED)
    report_b = service.evaluate_assurance(
        migration_id="dummy_b",
        source_execution=src_b,
        target_execution=tgt_b
    )
    assert report_b.final_status.name == "FAILED"
    print("  Test B (Assurance): TARGET_CAPABILITY_UNSUPPORTED -> FAILED ✓")

    # Test C: Ordinary missing column -> EXECUTION_ERROR
    print("  Test C is covered by test 'D  Missing column' above ✓")

    # Test D & E: APPROXIMATION always yields INCONCLUSIVE even if execution succeeds
    src_e = dummy_exec(ExecutionStatus.SUCCESS, conf="EXACT")
    tgt_e = dummy_exec(ExecutionStatus.SUCCESS, conf="APPROXIMATION")
    val_e = ValidationReport(
        validation_id="dummy_val",
        migration_id="dummy_e",
        source_execution_id="dummy_src",
        target_execution_id="dummy_tgt",
        overall_status="PASS",
        checks=[],
        summary_text="Match",
        discrepancy_categories={},
        is_order_dependent=False
    )
    dummy_trans = TranslationResult(
        status=TranslationStatus.SUCCESS,
        candidate_validation_status=CandidateValidationStatus.VALID_SYNTAX,
        response=TranslationResponse(target_sql="SELECT 1", translated_rules=[], skipped_rules=[]),
        metadata=TranslationMetadata(
            translation_id="dummy",
            migration_id="dummy",
            dataset_id="dummy",
            request_id="dummy",
            provider="dummy",
            model="dummy",
            source_dialect="dummy",
            target_dialect="dummy",
            source_sql_hash="dummy",
            translation_context_hash="dummy",
            prompt_hash="dummy",
            created_at="dummy",
        ),
    )
    
    report_e = service.evaluate_assurance(
        migration_id="dummy_e",
        translation_result=dummy_trans,
        source_execution=src_e,
        target_execution=tgt_e,
        validation_report=val_e
    )
    assert report_e.final_status.name == "INCONCLUSIVE"
    assert "insufficient semantic confidence" in report_e.decision_reason
    print("  Test D & E (Assurance): APPROXIMATION + Execution SUCCESS + Validation PASS -> INCONCLUSIVE ✓")

    print(f"  ✓ PASS")
    results.append(True)

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*70}")
    total = len(results)
    passed = sum(1 for r in results if r)
    print(f"  RESULTS: {passed}/{total} passed")
    print(f"{'='*70}")

    sys.exit(0 if all(results) else 1)
