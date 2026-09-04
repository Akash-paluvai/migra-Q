import os
import pytest
from backend.orchestrator.service import MigrationOrchestrator
from backend.orchestrator.models import PipelineRunRequest
from backend.db.database import Base, engine, get_db_session
from sqlalchemy import text

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Ensure mock DB tables exist and are cleaned up."""
    os.environ["POSTGRES_DB"] = "migraq_test"
    os.environ["POSTGRES_USER"] = "postgres"
    os.environ["POSTGRES_PASSWORD"] = "postgres"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"
    Base.metadata.create_all(bind=engine)
    with get_db_session() as db:
        try:
            db.execute(text("DELETE FROM migration_assurance_reports WHERE migration_id LIKE 'matrix_test_%'"))
            db.execute(text("DELETE FROM migration_records WHERE migration_id LIKE 'matrix_test_%'"))
            db.commit()
        except Exception:
            db.rollback()

@pytest.fixture
def orchestrator():
    return MigrationOrchestrator()

# Define the matrix
DIALECTS = [
    ("teradata", "bigquery"),
    ("teradata", "snowflake"),
    ("oracle", "bigquery"),
    ("oracle", "snowflake"),
    ("netezza", "bigquery"),
    ("netezza", "snowflake"),
]

def run_matrix_test(orchestrator, test_id, source_sql, source_dialect, target_dialect, expected_status, monkeypatch=None):
    from backend.translator.service import TranslationService
    from backend.translator.models import TranslationResult, TranslationStatus, TranslationMetadata, CandidateValidationStatus
    from backend.translator.models import TranslationResponse

    original_translate = TranslationService.translate

    def mock_translate(req, **kwargs):
        # We simulate perfect AST translation that fixes syntax to the target natively.
        # But for test E (sandbox limitation) we explicitly preserve HASHROW to trigger unsupported capability
        # For test D (approximation) we preserve TO_VARCHAR to trigger approximation confidence
        sql = req.source_sql
        if "matrix_test_b" in test_id:
            sql = sql.replace("ZEROIFNULL(a.balance)", "COALESCE(a.balance, 0)")
            sql = sql.replace("NULLIFZERO(c.credit_score)", "NULLIF(c.credit_score, 0)")
        elif "matrix_test_c2" in test_id:
            if "bigquery" in target_dialect:
                sql = sql.replace("NVL2(c.credit_score, 1, 0)", "IF(c.credit_score IS NOT NULL, 1, 0)")
            else:
                sql = sql.replace("NVL2(c.credit_score, 1, 0)", "IFF(c.credit_score IS NOT NULL, 1, 0)")
        elif "matrix_test_d" in test_id:
            # For test D (approximation) we translate to a valid target construct but one that 
            # will produce different results, triggering INCONCLUSIVE.
            sql = sql.replace("TO_VARCHAR(c.credit_score, '999,999.99')", "CAST(c.credit_score AS STRING)")
        elif "matrix_test_e" in test_id:
            # Trigger SANDBOX_LIMITATION by using a native target function that DuckDB lacks
            if "bigquery" in target_dialect:
                sql = sql.replace("HASHROW(c.customer_id, c.customer_segment)", "FARM_FINGERPRINT(c.customer_id)")
            else:
                sql = sql.replace("HASHROW(c.customer_id, c.customer_segment)", "PARSE_JSON('{}')")
        elif "matrix_test_f" in test_id:
            pass
            
        res = TranslationResult(
            status=TranslationStatus.SUCCESS,
            candidate_validation_status=CandidateValidationStatus.VALID_SYNTAX,
            response=TranslationResponse(target_sql=sql, assumptions=[], potential_risks=[], translated_rules=[]),
            metadata=TranslationMetadata(translation_id="x", request_id="x", provider="mock", model="mock", source_dialect=req.source_dialect, target_dialect=req.target_dialect, source_sql_hash="x", translation_context_hash="x", prompt_hash="x", created_at="x", duration_ms=1.0)
        )
        return res

    monkeypatch.setattr(TranslationService, "translate", mock_translate)

    req = PipelineRunRequest(
        migration_id=test_id,
        source_sql=source_sql,
        source_dialect=source_dialect,
        target_dialect=target_dialect,
        dataset_id="customer_risk",
        force_new=True,
    )
    report = orchestrator.run(req)
    assert report.assurance_report.final_status.name == expected_status, f"Expected {expected_status}, got {report.assurance_report.final_status.name} for {source_dialect}->{target_dialect}. Reason: {report.assurance_report.decision_reason}"


@pytest.mark.parametrize("source_dialect, target_dialect", DIALECTS)
def test_a_generic_sql(orchestrator, monkeypatch, source_dialect, target_dialect):
    sql = """
    SELECT
        c.customer_id,
        c.customer_segment,
        c.credit_score,
        CASE
            WHEN c.credit_score >= 700 THEN 'LOW_RISK'
            WHEN c.credit_score >= 600 THEN 'MEDIUM_RISK'
            ELSE 'HIGH_RISK'
        END AS calculated_risk
    FROM customers c
    WHERE c.status = 'ACTIVE'
    ORDER BY c.customer_id
    LIMIT 20
    """
    test_id = f"matrix_test_a_{source_dialect}_{target_dialect}"
    run_matrix_test(orchestrator, test_id, sql, source_dialect, target_dialect, "VERIFIED", monkeypatch)

@pytest.mark.parametrize("source_dialect, target_dialect", [("teradata", "bigquery"), ("teradata", "snowflake")])
def test_b_exact_adapter(orchestrator, monkeypatch, source_dialect, target_dialect):
    sql = """
    SELECT
        c.customer_id,
        ZEROIFNULL(a.balance) AS account_balance,
        NULLIFZERO(c.credit_score) AS normalized_credit_score
    FROM customers c
    LEFT JOIN accounts a
        ON c.customer_id = a.customer_id
    WHERE c.status = 'ACTIVE'
    """
    test_id = f"matrix_test_b_{source_dialect}_{target_dialect}"
    run_matrix_test(orchestrator, test_id, sql, source_dialect, target_dialect, "VERIFIED", monkeypatch)

@pytest.mark.parametrize("source_dialect, target_dialect", [("oracle", "bigquery"), ("oracle", "snowflake")])
def test_c_safe_equivalent_adapter(orchestrator, monkeypatch, source_dialect, target_dialect):
    sql = """
    SELECT
        c.customer_segment,
        NVL2(c.credit_score, 1, 0) AS has_score
    FROM customers c
    """
    test_id = f"matrix_test_c2_{source_dialect}_{target_dialect}"
    run_matrix_test(orchestrator, test_id, sql, source_dialect, target_dialect, "VERIFIED", monkeypatch)

@pytest.mark.parametrize("source_dialect, target_dialect", [("snowflake", "bigquery")])
def test_d_approximation(orchestrator, monkeypatch, source_dialect, target_dialect):
    # Testing Snowflake to Bigquery approximation logic
    sql = """
    SELECT
        c.customer_id,
        TO_VARCHAR(c.credit_score, '999,999.99') AS formatted_balance
    FROM customers c
    """
    test_id = f"matrix_test_d_{source_dialect}_{target_dialect}"
    run_matrix_test(orchestrator, test_id, sql, source_dialect, target_dialect, "INCONCLUSIVE", monkeypatch)

@pytest.mark.parametrize("source_dialect, target_dialect", [("teradata", "bigquery"), ("teradata", "snowflake")])
def test_e_sandbox_limitation(orchestrator, monkeypatch, source_dialect, target_dialect):
    sql = """
    SELECT HASHROW(c.customer_id, c.customer_segment) AS fingerprint FROM customers c LIMIT 10
    """
    test_id = f"matrix_test_e_{source_dialect}_{target_dialect}"
    run_matrix_test(orchestrator, test_id, sql, source_dialect, target_dialect, "INCONCLUSIVE", monkeypatch)

@pytest.mark.parametrize("source_dialect, target_dialect", DIALECTS)
def test_f_genuine_execution_error(orchestrator, monkeypatch, source_dialect, target_dialect):
    sql = """
    SELECT
        c.customer_id,
        c.DOES_NOT_EXIST
    FROM customers c;
    """
    test_id = f"matrix_test_f_{source_dialect}_{target_dialect}"
    # This triggers preflight error, returning BLOCKED
    run_matrix_test(orchestrator, test_id, sql, source_dialect, target_dialect, "BLOCKED", monkeypatch)


# ── Test G: Side Independence ────────────────────────────────────────
# Proves the critical architectural invariant:
#   Target SANDBOX_LIMITATION does NOT leak to source.
#   Source and target carry independent dialect/status/diagnostics.
#
# For every dialect pair:
#   - Source SQL: clean, DuckDB-executable SQL
#   - Target SQL (mocked): contains a function DuckDB cannot execute
# Asserts:
#   - source_exec.dialect == source_dialect
#   - target_exec.dialect == target_dialect
#   - source_exec.status == SUCCESS
#   - target_exec.status == SANDBOX_LIMITATION
#   - assurance == INCONCLUSIVE (generic, no pair-specific logic)

@pytest.mark.parametrize("source_dialect, target_dialect", DIALECTS)
def test_g_side_independence(orchestrator, monkeypatch, source_dialect, target_dialect):
    """Target SANDBOX_LIMITATION must NOT leak to source execution."""
    from backend.translator.service import TranslationService
    from backend.translator.models import TranslationResult, TranslationStatus, TranslationMetadata, CandidateValidationStatus
    from backend.translator.models import TranslationResponse
    from backend.execution.service import ExecutionService
    from backend.execution.models import ExecutionRequest, ExecutionResult, ExecutionMode

    # Clean source SQL — DuckDB can execute this
    source_sql = """
    SELECT c.customer_id, c.credit_score
    FROM customers c
    WHERE c.status = 'ACTIVE'
    ORDER BY c.customer_id
    LIMIT 10
    """

    # Target SQL contains a function DuckDB cannot execute.
    # FARM_FINGERPRINT is used for all targets — it's not DuckDB-native and
    # SQLGlot passes it through as-is. The test mocks translation, so the
    # function doesn't need to be native to the target dialect.
    target_sql = "SELECT FARM_FINGERPRINT(CAST(c.customer_id AS STRING)) AS h FROM customers c LIMIT 10"

    # Mock translator to return the un-sandboxable target SQL
    def mock_translate(req, **kwargs):
        return TranslationResult(
            status=TranslationStatus.SUCCESS,
            candidate_validation_status=CandidateValidationStatus.VALID_SYNTAX,
            response=TranslationResponse(target_sql=target_sql, assumptions=[], potential_risks=[], translated_rules=[]),
            metadata=TranslationMetadata(translation_id="x", request_id="x", provider="mock", model="mock", source_dialect=req.source_dialect, target_dialect=req.target_dialect, source_sql_hash="x", translation_context_hash="x", prompt_hash="x", created_at="x", duration_ms=1.0)
        )
    monkeypatch.setattr(TranslationService, "translate", mock_translate)

    # Capture individual execution results
    captured_executions: list[ExecutionResult] = []
    original_execute = ExecutionService.execute

    def capturing_execute(request: ExecutionRequest) -> ExecutionResult:
        result = original_execute(request)
        captured_executions.append(result)
        return result

    monkeypatch.setattr(ExecutionService, "execute", capturing_execute)

    test_id = f"matrix_test_g_{source_dialect}_{target_dialect}"
    req = PipelineRunRequest(
        migration_id=test_id,
        source_sql=source_sql,
        source_dialect=source_dialect,
        target_dialect=target_dialect,
        dataset_id="customer_risk",
        force_new=True,
    )
    report = orchestrator.run(req)

    # Find source and target execution results
    src_exec = next((e for e in captured_executions if e.execution_mode == ExecutionMode.SOURCE), None)
    tgt_exec = next((e for e in captured_executions if e.execution_mode == ExecutionMode.TARGET), None)

    assert src_exec is not None, "Source execution result not captured"
    assert tgt_exec is not None, "Target execution result not captured"

    # ── Core side-independence assertions ──
    # 1. Each result carries its own dialect
    assert src_exec.dialect == source_dialect, f"Source dialect mismatch: expected {source_dialect}, got {src_exec.dialect}"
    assert tgt_exec.dialect == target_dialect, f"Target dialect mismatch: expected {target_dialect}, got {tgt_exec.dialect}"

    # 2. Source succeeded independently of target
    assert src_exec.status.value == "SUCCESS", f"Source should be SUCCESS but got {src_exec.status.value}"

    # 3. Target hit sandbox limitation independently of source
    assert tgt_exec.status.value == "SANDBOX_LIMITATION", f"Target should be SANDBOX_LIMITATION but got {tgt_exec.status.value}"

    # 4. Assurance is INCONCLUSIVE (generic decision, not pair-specific)
    assert report.assurance_report.final_status.name == "INCONCLUSIVE", \
        f"Expected INCONCLUSIVE, got {report.assurance_report.final_status.name}. Reason: {report.assurance_report.decision_reason}"

    # 5. Execution summary carries per-side dialect
    exec_summary = report.assurance_report.execution_summary
    assert exec_summary is not None, "ExecutionSummary should exist"
    assert exec_summary.source_dialect == source_dialect, f"Summary source_dialect mismatch: {exec_summary.source_dialect}"
    assert exec_summary.target_dialect == target_dialect, f"Summary target_dialect mismatch: {exec_summary.target_dialect}"

