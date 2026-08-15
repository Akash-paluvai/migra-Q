"""RepairExecutor — adapter executing candidate repaired SQL through Phase 3 ExecutionService."""

from __future__ import annotations

from backend.execution.models import ExecutionRequest, ExecutionResult, ExecutionStatus
from backend.execution.service import ExecutionService
from backend.repair_verification.exceptions import ExecutionFailedError


class RepairExecutor:
    """Executes repaired SQL through Phase 3 SandboxExecutor without modifying Phase 3 logic."""

    @classmethod
    def execute_repaired_sql(
        cls,
        proposed_sql: str,
        dataset_id: str,
        target_dialect: str = "bigquery",
        execution_mode: str = "TARGET",
    ) -> ExecutionResult:
        """Execute proposed repair SQL using Phase 3 ExecutionService.

        Raises ExecutionFailedError if runtime execution fails.
        """
        request = ExecutionRequest(
            sql=proposed_sql,
            dialect=target_dialect,
            dataset_id=dataset_id,
            execution_mode=execution_mode,  # type: ignore[arg-type]
        )

        result = ExecutionService.execute(request)

        if result.status != ExecutionStatus.SUCCESS:
            raise ExecutionFailedError(
                error_code=result.error_code or "EXECUTION_FAILED",
                error_message=result.error_message or "Repaired SQL query execution failed in DuckDB sandbox.",
            )

        return result
