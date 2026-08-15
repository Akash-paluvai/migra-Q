"""Phase 10.1 Dataset Workbench Data Models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    """Schema specification for a single column in a dataset table."""

    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type (e.g. VARCHAR, INTEGER, TIMESTAMP)")
    nullable: bool = Field(default=True, description="Whether column allows NULL values")
    ordinal_position: int = Field(default=0, description="1-based column position")
    primary_key: bool = Field(default=False, description="Whether column is part of primary key")
    description: str | None = Field(default=None, description="Optional column description")
    sample_values: list[Any] = Field(default_factory=list, description="Sample values for column")


class DatasetTableSummary(BaseModel):
    """Summary of a single table in a dataset."""

    table_name: str = Field(..., description="Table name")
    row_count: int = Field(..., description="Total row count in table")
    columns: list[ColumnSchema] = Field(default_factory=list, description="Column schemas")


class DatasetSummary(BaseModel):
    """Lightweight summary of a registered dataset."""

    dataset_id: str = Field(..., description="Unique dataset identifier")
    display_name: str = Field(..., description="Human-readable dataset display name")
    description: str = Field(default="", description="Dataset summary description")
    source: str = Field(default="synthetic", description="Source origin (builtin, upload, lab)")
    profile: str = Field(default="dev", description="Generation profile (dev, test, prod)")
    row_count_total: int = Field(default=0, description="Total aggregated row count across tables")
    table_count: int = Field(default=0, description="Number of tables in dataset")
    size_bytes: int = Field(default=0, description="Total size in bytes")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")
    dataset_hash: str = Field(..., description="Deterministic SHA256 content/schema hash")
    schema_version: str = Field(default="1.0", description="Dataset schema version")
    is_builtin: bool = Field(default=True, description="Whether dataset is built-in benchmark")
    is_upload: bool = Field(default=False, description="Whether dataset was uploaded by user")
    status: str = Field(default="READY", description="Dataset status (READY, INDEXING, ERROR)")
    tags: list[str] = Field(default_factory=list, description="Domain tags (e.g. boundary, aggregation)")


class DatasetDetail(DatasetSummary):
    """Detailed metadata specification for a dataset including table schemas."""

    table_summaries: list[DatasetTableSummary] = Field(default_factory=list, description="Summaries per table")
    manifest_path: str | None = Field(default=None, description="Path to dataset manifest")


class DatasetPreviewResponse(BaseModel):
    """Response returned when requesting a sample row preview for a dataset table."""

    dataset_id: str
    table_name: str
    total_rows: int
    returned_rows: int
    columns: list[ColumnSchema]
    rows: list[dict[str, Any]]
