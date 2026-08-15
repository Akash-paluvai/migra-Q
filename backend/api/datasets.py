"""Phase 10.1 Dataset Workbench REST API Endpoints."""

from __future__ import annotations

import shutil
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.datasets.models import (
    DatasetDetail,
    DatasetPreviewResponse,
    DatasetSummary,
    DatasetTableSummary,
)
from backend.datasets.registry import UPLOADS_DIR, DatasetRegistry
from backend.datasets.upload import DatasetUploadError, DatasetUploadHandler

datasets_router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])
_registry = DatasetRegistry()


@datasets_router.get("", response_model=list[DatasetSummary])
def list_datasets() -> list[DatasetSummary]:
    """Retrieve summaries for all registered datasets (built-in and uploaded)."""
    return _registry.list_datasets()


@datasets_router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(dataset_id: str) -> DatasetDetail:
    """Retrieve detailed dataset metadata including table schemas."""
    detail = _registry.get_dataset(dataset_id)
    if detail is None:
        raise HTTPException(
            status_code=404, detail=f"Dataset '{dataset_id}' not found."
        )
    return detail


@datasets_router.get("/{dataset_id}/schema", response_model=list[DatasetTableSummary])
def get_dataset_schema(dataset_id: str) -> list[DatasetTableSummary]:
    """Retrieve table schemas and column specifications for a dataset."""
    if not _registry.exists(dataset_id):
        raise HTTPException(
            status_code=404, detail=f"Dataset '{dataset_id}' not found."
        )
    return _registry.resolve_schema(dataset_id)


@datasets_router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def get_dataset_preview(
    dataset_id: str,
    table: str | None = None,
    limit: int = 100,
) -> DatasetPreviewResponse:
    """Retrieve sample row preview for a dataset table (max limit 100 rows)."""
    if not _registry.exists(dataset_id):
        raise HTTPException(
            status_code=404, detail=f"Dataset '{dataset_id}' not found."
        )
    return _registry.resolve_preview(dataset_id=dataset_id, table_name=table, limit=limit)


@datasets_router.post("/upload", response_model=DatasetDetail)
def upload_dataset(
    file: UploadFile = File(...),
    display_name: str | None = Form(None),
    description: str | None = Form(None),
) -> DatasetDetail:
    """Upload a new CSV, Parquet, or ZIP dataset."""
    try:
        detail = DatasetUploadHandler.process_upload(
            file_obj=file.file,
            filename=file.filename or "upload.csv",
            display_name=display_name,
            description=description,
        )
        _registry.register_dataset(detail)
        return detail
    except DatasetUploadError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to process dataset upload: {exc}"
        )


@datasets_router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str) -> dict[str, Any]:
    """Remove or unregister an uploaded dataset."""
    detail = _registry.get_dataset(dataset_id)
    if detail is None:
        raise HTTPException(
            status_code=404, detail=f"Dataset '{dataset_id}' not found."
        )

    if detail.is_builtin:
        raise HTTPException(
            status_code=400, detail="Cannot delete built-in benchmark datasets."
        )

    upload_dir = UPLOADS_DIR / dataset_id
    if upload_dir.exists():
        shutil.rmtree(upload_dir, ignore_errors=True)

    return {"status": "DELETED", "dataset_id": dataset_id}
