"""FastAPI execution endpoints."""

from fastapi import APIRouter, HTTPException

from backend.execution.models import ExecutionRequest, ExecutionResult
from backend.execution.service import ExecutionService

router = APIRouter()


@router.post("/api/v1/executions", response_model=ExecutionResult)
def create_execution(req: ExecutionRequest) -> ExecutionResult:
    """Execute a SQL query independently in the DuckDB sandbox environment."""
    try:
        return ExecutionService.execute(req)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/api/v1/executions/{execution_id}", response_model=ExecutionResult)
def get_execution(execution_id: str) -> ExecutionResult:
    """Retrieve execution metadata by execution_id."""
    res = ExecutionService.get_execution(execution_id)
    if res is None:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")
    return res
