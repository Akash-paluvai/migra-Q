"""DuckDB execution runner with in-memory isolation, timing, and timeout bounds."""

import concurrent.futures
import time
import uuid
from datetime import datetime, timezone

import duckdb

from backend.execution.dataset_loader import ResolvedDataset
from backend.execution.exceptions import (
    DatasetError,
    SecurityViolationError,
)
from backend.execution.hashing import hash_query
from backend.execution.models import (
    ExecutionMode,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
)
from backend.execution.query_normalizer import validate_read_only_query
from backend.execution.result_capture import capture_and_persist_result

EXECUTION_TIMEOUT_SECONDS = 10.0


def _raw_execute_task(
    sql: str,
    execution_id: str,
    dataset_dir_str: str,
    query_hash: str,
    dataset_id: str,
    dataset_hash: str,
    execution_mode: ExecutionMode,
) -> dict:
    """Internal task executed in isolated DuckDB connection."""
    # Create fresh isolated in-memory DuckDB connection
    conn = duckdb.connect(":memory:")
    try:
        # Load and register dataset views
        from backend.execution.dataset_loader import resolve_dataset

        res_dataset = resolve_dataset(dataset_dir_str)
        res_dataset.register_views(conn)

        start_time = time.perf_counter()
        captured = capture_and_persist_result(
            conn=conn,
            sql=sql,
            execution_id=execution_id,
            query_hash=query_hash,
            dataset_id=dataset_id,
            dataset_hash=dataset_hash,
            duration_ms=0.0,  # Updated below
        )
        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return {
            "status": ExecutionStatus.SUCCESS,
            "duration_ms": duration_ms,
            "row_count": captured["row_count"],
            "columns": captured["columns"],
            "sample_data": captured["sample_data"],
            "sample_is_ordered": captured["sample_is_ordered"],
            "result_artifact": captured["result_artifact"],
            "error_code": None,
            "error_message": None,
        }
    finally:
        conn.close()


def run_duckdb_execution(
    request: ExecutionRequest, resolved_dataset: ResolvedDataset
) -> ExecutionResult:
    """Execute a read-only query against a resolved dataset inside an isolated DuckDB runner."""
    execution_id = str(uuid.uuid4())
    now_utc = datetime.now(timezone.utc).isoformat()

    # 1. Enforce read-only security policy
    try:
        validate_read_only_query(request.sql)
    except SecurityViolationError as exc:
        return ExecutionResult(
            execution_id=execution_id,
            query_hash=hash_query(request.sql),
            dataset_id=resolved_dataset.dataset_id,
            dataset_hash=resolved_dataset.dataset_hash,
            execution_mode=request.execution_mode,
            status=ExecutionStatus.SECURITY_ERROR,
            timestamp=now_utc,
            duration_ms=0.0,
            row_count=0,
            error_code="SECURITY_VIOLATION",
            error_message=str(exc),
        )

    q_hash = hash_query(request.sql)

    import json
    import sqlglot
    from sqlglot import expressions as exp
    from backend.execution.exceptions import ExecutionTranspilationError
    from backend.execution.dialect_transforms import analyze_and_transform
    from backend.execution.dialect_transforms.base import SemanticConfidence

    import logging
    logger = logging.getLogger(__name__)

    try:
        parsed = sqlglot.parse_one(request.sql, read=request.dialect)
        analysis = analyze_and_transform(parsed, request.dialect)
        executable_sql = analysis.transformed_ast.sql(dialect="duckdb")
        compatibility_confidence = analysis.aggregate_confidence.value

        logger.info(
            "DuckDB executable SQL [%s] (confidence=%s):\n%s",
            request.dialect,
            compatibility_confidence,
            executable_sql,
        )
    except Exception as exc:
        err = ExecutionTranspilationError(f"Could not transpile {request.dialect} SQL to DuckDB: {exc}")
        return ExecutionResult(
            execution_id=execution_id,
            query_hash=q_hash,
            dataset_id=resolved_dataset.dataset_id,
            dataset_hash=resolved_dataset.dataset_hash,
            execution_mode=request.execution_mode,
            status=ExecutionStatus.EXECUTION_ERROR,
            timestamp=now_utc,
            duration_ms=0.0,
            row_count=0,
            error_code="TRANSPILATION_ERROR",
            error_message=str(err),
        )

    # ── Pre-execution capability check ────────────────────────────
    # If the compatibility analysis determined the AST is not executable
    # (e.g., contains unresolvable dialect constructs), short-circuit
    # before touching DuckDB. DuckDB errors remain a fallback safety net.
    if not analysis.executable:
        return ExecutionResult(
            execution_id=execution_id,
            query_hash=q_hash,
            dataset_id=resolved_dataset.dataset_id,
            dataset_hash=resolved_dataset.dataset_hash,
            execution_mode=request.execution_mode,
            status=ExecutionStatus.UNSUPPORTED_CAPABILITY,
            timestamp=now_utc,
            duration_ms=0.0,
            row_count=0,
            error_code="SANDBOX_PRE_EXECUTION_UNSUPPORTED",
            error_message=json.dumps({
                "error_code": "SANDBOX_PRE_EXECUTION_UNSUPPORTED",
                "dialect": request.dialect,
                "execution_engine": "duckdb",
                "aggregate_confidence": compatibility_confidence,
                "diagnostics": analysis.diagnostics,
                "message": (
                    "Compatibility analysis determined this query cannot "
                    "be safely executed in the DuckDB sandbox."
                ),
            }, indent=2),
            compatibility_confidence=compatibility_confidence,
        )

    # 2. Execute within timeout boundary using ThreadPoolExecutor/Process
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            _raw_execute_task,
            executable_sql,
            execution_id,
            str(resolved_dataset.dataset_dir),
            q_hash,
            resolved_dataset.dataset_id,
            resolved_dataset.dataset_hash,
            request.execution_mode,
        )
        try:
            res_dict = future.result(timeout=EXECUTION_TIMEOUT_SECONDS)
            logger.info("Phase 3 execution result (dialect=%s): status=%s error=%s", request.dialect, res_dict["status"], res_dict["error_message"])
            return ExecutionResult(
                execution_id=execution_id,
                query_hash=q_hash,
                dataset_id=resolved_dataset.dataset_id,
                dataset_hash=resolved_dataset.dataset_hash,
                execution_mode=request.execution_mode,
                status=res_dict["status"],
                timestamp=now_utc,
                duration_ms=res_dict["duration_ms"],
                row_count=res_dict["row_count"],
                columns=res_dict["columns"],
                sample_data=res_dict["sample_data"],
                sample_is_ordered=res_dict["sample_is_ordered"],
                result_artifact=res_dict["result_artifact"],
                error_code=res_dict["error_code"],
                error_message=res_dict["error_message"],
                compatibility_confidence=compatibility_confidence,
            )
        except concurrent.futures.TimeoutError:
            return ExecutionResult(
                execution_id=execution_id,
                query_hash=q_hash,
                dataset_id=resolved_dataset.dataset_id,
                dataset_hash=resolved_dataset.dataset_hash,
                execution_mode=request.execution_mode,
                status=ExecutionStatus.TIMEOUT,
                timestamp=now_utc,
                duration_ms=EXECUTION_TIMEOUT_SECONDS * 1000.0,
                row_count=0,
                error_code="TIMEOUT",
                error_message=f"Query timed out after {EXECUTION_TIMEOUT_SECONDS}s.",
                compatibility_confidence=compatibility_confidence,
            )
        except Exception as exc:
            import re
            import json

            err_type = ExecutionStatus.EXECUTION_ERROR
            error_code = type(exc).__name__
            error_message = str(exc)

            if isinstance(exc, DatasetError):
                err_type = ExecutionStatus.DATASET_ERROR

            else:
                # ── Pattern-first classification ──────────────────────────
                # Only the specific regex match determines classification.
                # We never use broad "Binder Error" / "Catalog Error" as
                # the trigger — those categories cover far more than
                # missing functions.

                missing_func = re.search(
                    r"Scalar Function with name ([a-zA-Z_][a-zA-Z0-9_]*) does not exist",
                    error_message,
                    re.IGNORECASE,
                )

                signature_mismatch = re.search(
                    r"No function matches the given name and argument types "
                    r"'([a-zA-Z_][a-zA-Z0-9_]*)\(",
                    error_message,
                    re.IGNORECASE,
                )

                if missing_func:
                    # ── Case 1: Function genuinely missing from DuckDB ────
                    # DuckDB has no implementation at all. This is a clear
                    # sandbox capability gap.
                    func_name = missing_func.group(1)
                    err_type = ExecutionStatus.UNSUPPORTED_CAPABILITY
                    error_code = "SANDBOX_UNSUPPORTED_FUNCTION"
                    error_message = json.dumps({
                        "error_code": error_code,
                        "dialect": request.dialect,
                        "function": func_name,
                        "execution_engine": "duckdb",
                        "message": (
                            "The DuckDB sandbox could not execute this "
                            "expression because no compatible execution "
                            "strategy was available for this function."
                        ),
                        "raw_error": str(exc),
                    }, indent=2)

                elif signature_mismatch:
                    # ── Case 2: Function exists, but signature incompatible ─
                    # DuckDB knows the function name but can't match the
                    # argument signature. This could be:
                    #   (a) a dialect-specific overload DuckDB lacks, or
                    #   (b) genuinely invalid SQL in any dialect.
                    #
                    # Source-dialect validation: re-parse the original SQL
                    # and check whether the function is dialect-proprietary
                    # (exp.Anonymous) or a standard function (native AST node).
                    func_name = signature_mismatch.group(1)
                    is_dialect_specific = _is_function_dialect_specific(
                        request.sql, request.dialect, func_name
                    )

                    if is_dialect_specific:
                        # Dialect-proprietary function whose signature
                        # DuckDB can't match → sandbox capability gap.
                        err_type = ExecutionStatus.UNSUPPORTED_CAPABILITY
                        error_code = "SANDBOX_UNSUPPORTED_FUNCTION_SIGNATURE"
                        error_message = json.dumps({
                            "error_code": error_code,
                            "dialect": request.dialect,
                            "function": func_name,
                            "execution_engine": "duckdb",
                            "message": (
                                "The DuckDB sandbox could not match the "
                                "argument signature for this dialect-specific "
                                "function. The original expression may be "
                                "valid in the source dialect."
                            ),
                            "raw_error": str(exc),
                        }, indent=2)
                    else:
                        # Standard function with wrong arguments — likely
                        # bad SQL, not a sandbox limitation.
                        error_code = "SANDBOX_FUNCTION_SIGNATURE_MISMATCH"
                        error_message = json.dumps({
                            "error_code": error_code,
                            "dialect": request.dialect,
                            "function": func_name,
                            "execution_engine": "duckdb",
                            "message": (
                                "DuckDB could not find a matching overload "
                                "for this standard function with the given "
                                "argument types. This likely indicates "
                                "invalid SQL rather than a sandbox limitation."
                            ),
                            "raw_error": str(exc),
                        }, indent=2)
                        # err_type stays EXECUTION_ERROR.

                # ── Case 3: Everything else ───────────────────────────────
                # Missing columns, invalid expressions, type mismatches,
                # ambiguous references, malformed SQL, etc.
                # err_type stays EXECUTION_ERROR, error_code stays as the
                # Python exception class name, error_message stays raw.

            return ExecutionResult(
                execution_id=execution_id,
                query_hash=q_hash,
                dataset_id=resolved_dataset.dataset_id,
                dataset_hash=resolved_dataset.dataset_hash,
                execution_mode=request.execution_mode,
                status=err_type,
                timestamp=now_utc,
                duration_ms=0.0,
                row_count=0,
                error_code=error_code,
                error_message=error_message,
                compatibility_confidence=compatibility_confidence,
            )


def _is_function_dialect_specific(original_sql: str, dialect: str, func_name: str) -> bool:
    """Check whether a function is dialect-specific by examining the source AST.

    If SQLGlot parses the function as an ``exp.Anonymous`` node, it means
    SQLGlot has no native knowledge of this function — strongly suggesting
    it's a dialect-proprietary construct (e.g., Teradata ZEROIFNULL, Oracle NVL2).

    If SQLGlot parses it as a native expression type (e.g., ``exp.Substring``
    for ``substr``), then the function is standard SQL and a signature mismatch
    is most likely invalid SQL, not a sandbox limitation.

    This prevents the sandbox from becoming the authority on SQL validity:
    DuckDB alone cannot establish whether a call is valid in the source dialect.

    Returns True if the function appears to be dialect-specific.
    Returns False if it's a standard/known function, or if parsing fails.
    """
    try:
        import sqlglot
        from sqlglot import expressions as exp

        parsed = sqlglot.parse_one(original_sql, read=dialect)
        for node in parsed.walk():
            if isinstance(node, exp.Anonymous) and node.name.lower() == func_name.lower():
                return True
        return False
    except Exception:
        # If we can't parse, we can't validate — safe default.
        return False
