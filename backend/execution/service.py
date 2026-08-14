"""ExecutionService — service layer orchestrating query execution, auditing, and storage."""

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.core.logging import get_logger
from backend.db.database import SessionLocal, check_database_health
from backend.db.models import ExecutionRecord
from backend.execution.models import ExecutionRequest, ExecutionResult
from backend.execution.sandbox import SandboxExecutor

logger = get_logger(__name__)


class ExecutionService:
    """Service layer managing query executions and persistence."""

    @staticmethod
    def execute(request: ExecutionRequest) -> ExecutionResult:
        """Execute a query through the sandbox and persist metadata to PostgreSQL and disk."""
        result = SandboxExecutor.execute(request)

        # Log metadata to PostgreSQL if available
        ExecutionService._persist_to_db(result)

        return result

    @staticmethod
    def get_execution(execution_id: str) -> ExecutionResult | None:
        """Retrieve execution metadata by ID from PostgreSQL or local disk runtime results."""
        # 1. Try DB first
        if check_database_health():
            db: Session = SessionLocal()
            try:
                rec = (
                    db.query(ExecutionRecord)
                    .filter(ExecutionRecord.execution_id == execution_id)
                    .first()
                )
                if rec:
                    meta_dict = json.loads(rec.metadata_json) if rec.metadata_json else {}
                    return ExecutionResult(
                        execution_id=rec.execution_id,
                        query_hash=rec.query_hash,
                        dataset_id=rec.dataset_id,
                        dataset_hash=rec.dataset_hash,
                        execution_mode=rec.execution_mode,
                        status=rec.status,
                        timestamp=rec.started_at.isoformat(),
                        duration_ms=rec.duration_ms,
                        row_count=rec.row_count,
                        columns=meta_dict.get("columns", []),
                        sample_data=meta_dict.get("sample_data", None),
                        sample_is_ordered=meta_dict.get("sample_is_ordered", False),
                        result_artifact=rec.result_artifact,
                        error_code=rec.error_code,
                        error_message=rec.error_message,
                        engine=rec.engine,
                        engine_version=rec.engine_version,
                    )
            except Exception as exc:
                logger.warning("Error fetching execution from DB: %s", exc)
            finally:
                db.close()

        # 2. Fall back to local disk metadata artifact
        meta_path = Path.cwd() / "datasets" / "runtime_results" / execution_id / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return ExecutionResult(
                    execution_id=data["execution_id"],
                    query_hash=data["query_hash"],
                    dataset_id=data["dataset_id"],
                    dataset_hash=data["dataset_hash"],
                    execution_mode=data.get("execution_mode", "SOURCE"),
                    status=data["status"],
                    timestamp=data["timestamp"],
                    duration_ms=data["duration_ms"],
                    row_count=data["row_count"],
                    columns=data.get("columns", []),
                    sample_data=data.get("sample_data", None),
                    sample_is_ordered=data.get("sample_is_ordered", False),
                    result_artifact=data.get("result_artifact", None),
                    error_code=data.get("error_code", None),
                    error_message=data.get("error_message", None),
                    engine=data.get("engine", "duckdb"),
                    engine_version=data.get("engine_version", "1.0"),
                )
            except Exception as exc:
                logger.warning("Error reading metadata.json from disk: %s", exc)

        return None

    @staticmethod
    def compare_inputs(
        source_sql: str,
        target_sql: str,
        dataset_id: str,
        dataset_dir: str | None = None,
    ) -> tuple[ExecutionResult, ExecutionResult]:
        """Execute source and target queries independently against the same dataset.

        Does NOT determine semantic equivalence (Phase 4 responsibility).
        Returns (source_execution_result, target_execution_result).
        """
        req_source = ExecutionRequest(
            sql=source_sql,
            dataset_id=dataset_id,
            dataset_dir=dataset_dir,
            execution_mode="SOURCE",
            label="source_candidate",
        )
        req_target = ExecutionRequest(
            sql=target_sql,
            dataset_id=dataset_id,
            dataset_dir=dataset_dir,
            execution_mode="TARGET",
            label="target_candidate",
        )

        res_source = ExecutionService.execute(req_source)
        res_target = ExecutionService.execute(req_target)

        return res_source, res_target

    @staticmethod
    def _persist_to_db(result: ExecutionResult) -> None:
        """Persist execution audit record to PostgreSQL if reachable."""
        if not check_database_health():
            return
        db: Session = SessionLocal()
        try:
            meta_json = json.dumps(
                {
                    "columns": [c.model_dump() for c in result.columns],
                    "sample_data": result.sample_data,
                    "sample_is_ordered": result.sample_is_ordered,
                }
            )
            rec = ExecutionRecord(
                execution_id=result.execution_id,
                query_hash=result.query_hash,
                dataset_id=result.dataset_id,
                dataset_hash=result.dataset_hash,
                execution_mode=result.execution_mode,
                status=result.status,
                engine=result.engine,
                engine_version=result.engine_version,
                duration_ms=result.duration_ms,
                row_count=result.row_count,
                result_artifact=result.result_artifact,
                error_code=result.error_code,
                error_message=result.error_message,
                metadata_json=meta_json,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            db.add(rec)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning("Failed to persist execution record to DB: %s", exc)
        finally:
            db.close()
