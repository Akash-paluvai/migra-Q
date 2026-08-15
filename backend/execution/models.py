"""Pydantic domain models for query execution requests, status, and results."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    SOURCE = "SOURCE"
    TARGET = "TARGET"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    DATASET_ERROR = "DATASET_ERROR"
    SECURITY_ERROR = "SECURITY_ERROR"
    TIMEOUT = "TIMEOUT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ColumnSchema(BaseModel):
    name: str
    type: str


class ExecutionRequest(BaseModel):
    sql: str
    dialect: str = "duckdb"
    dataset_id: str = "dev"
    dataset_dir: str | None = None
    execution_mode: ExecutionMode = ExecutionMode.SOURCE
    migration_id: str | None = None
    label: str | None = None

class ExecutionResult(BaseModel):
    execution_id: str
    query_hash: str
    dataset_id: str
    dataset_hash: str
    execution_mode: ExecutionMode = ExecutionMode.SOURCE
    status: ExecutionStatus
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: float = 0.0
    row_count: int = 0
    columns: list[ColumnSchema] = Field(default_factory=list)
    sample_data: list[dict[str, Any]] | None = None
    sample_is_ordered: bool = False
    result_artifact: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    engine: str = "duckdb"
    engine_version: str = "1.0"
