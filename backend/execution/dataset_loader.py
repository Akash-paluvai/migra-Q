"""Dataset loader for resolving Phase 2 manifest datasets and exposing them to DuckDB."""

import json
from pathlib import Path
from typing import Any

import duckdb

from backend.execution.exceptions import DatasetError
from backend.execution.hashing import hash_dataset_manifest


class ResolvedDataset:
    """Represents a validated Phase 2 dataset ready for DuckDB registration."""

    def __init__(
        self, dataset_id: str, dataset_dir: Path, manifest: dict[str, Any], dataset_hash: str
    ):
        self.dataset_id = dataset_id
        self.dataset_dir = dataset_dir
        self.manifest = manifest
        self.dataset_hash = dataset_hash

    def register_views(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Register Parquet files as read-only views in DuckDB."""
        file_names = self.manifest.get("file_names", {})
        if not file_names:
            raise DatasetError(
                f"No file_names specified in manifest for dataset '{self.dataset_id}'."
            )

        for table_name, file_name in file_names.items():
            file_path = self.dataset_dir / file_name
            if not file_path.exists():
                raise DatasetError(f"Dataset file missing for table '{table_name}': {file_path}")

            # Register as read-only view querying the Parquet file directly
            view_sql = (
                f"CREATE VIEW {table_name} AS SELECT * FROM read_parquet('{file_path.resolve()}');"
            )
            try:
                conn.execute(view_sql)
            except Exception as exc:
                raise DatasetError(
                    f"Failed to register view for table '{table_name}': {exc}"
                ) from exc


def resolve_dataset(dataset_id_or_path: str) -> ResolvedDataset:
    """Resolve a dataset by ID or directory path.

    Searches:
    1. Direct directory path (if dataset_id_or_path is a valid path)
    2. datasets/generated/<dataset_id_or_path>
    3. datasets/scenarios/<dataset_id_or_path>
    """
    target_dir: Path | None = None
    candidate_path = Path(dataset_id_or_path)

    if candidate_path.is_dir() and (candidate_path / "manifest.json").exists():
        target_dir = candidate_path
    else:
        # Search relative to repository root
        root = Path.cwd()
        possible_dirs = [
            root / "datasets" / "generated" / dataset_id_or_path,
            root / "datasets" / "scenarios" / dataset_id_or_path,
            root / dataset_id_or_path,
        ]
        for p in possible_dirs:
            if p.is_dir() and (p / "manifest.json").exists():
                target_dir = p
                break

    if target_dir is None or not target_dir.exists():
        raise DatasetError(f"Dataset '{dataset_id_or_path}' not found or missing manifest.json.")

    manifest_path = target_dir / "manifest.json"
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as exc:
        raise DatasetError(f"Failed to parse manifest.json at {manifest_path}: {exc}") from exc

    dataset_id = manifest.get("dataset_id", dataset_id_or_path)
    dataset_hash = hash_dataset_manifest(manifest)

    return ResolvedDataset(
        dataset_id=dataset_id,
        dataset_dir=target_dir,
        manifest=manifest,
        dataset_hash=dataset_hash,
    )
