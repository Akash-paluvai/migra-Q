"""Sandbox execution boundary interface.

Phase 3 Security Guarantees:
1. SQL queries execute strictly against embedded DuckDB in-memory connections.
2. Read-only validation prevents INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, COPY, INSTALL, LOAD.
3. PostgreSQL database credentials and secrets are NEVER exposed to the SQL execution environment.
4. Source Phase 2 Parquet datasets are mounted as read-only views and are NEVER mutated.
5. Process/thread timeout bounds prevent infinite execution loops.
"""

from backend.execution.dataset_loader import resolve_dataset
from backend.execution.duckdb_runner import run_duckdb_execution
from backend.execution.models import ExecutionRequest, ExecutionResult


class SandboxExecutor:
    """Isolated execution sandbox entry point."""

    @staticmethod
    def execute(request: ExecutionRequest) -> ExecutionResult:
        """Resolve dataset and execute query inside isolated DuckDB runner."""
        dataset_target = request.dataset_dir or request.dataset_id
        resolved_ds = resolve_dataset(dataset_target)
        return run_duckdb_execution(request, resolved_ds)
