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

    import sqlglot
    from sqlglot import expressions as exp
    from backend.execution.exceptions import ExecutionTranspilationError
    from backend.execution.dialect_transforms import transform_for_duckdb

    import logging
    logger = logging.getLogger(__name__)

    try:
        parsed = sqlglot.parse_one(request.sql, read=request.dialect)
        transformed = parsed.transform(lambda node: transform_for_duckdb(node, request.dialect))
        executable_sql = transformed.sql(dialect="duckdb")
        
        logger.info(
            "DuckDB executable SQL [%s]:\n%s",
            request.dialect,
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
            )
        except Exception as exc:
            err_type = ExecutionStatus.EXECUTION_ERROR
            if isinstance(exc, DatasetError):
                err_type = ExecutionStatus.DATASET_ERROR
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
                error_code=type(exc).__name__,
                error_message=str(exc),
            )
