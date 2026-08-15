"""Phase 10.1 Dataset Upload Handler.

Handles user file uploads (CSV, Parquet, ZIP) with security controls:
- Zip-Slip path traversal protection
- Executable content rejection (.exe, .sh, .py, .js, etc.)
- Strict table naming (basename without extension, normalized to snake_case)
- Table name collision checks (e.g. transactions.csv and transactions.parquet)
- File size limit enforcement (max 50MB)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import duckdb

from backend.core.logging import get_logger
from backend.datasets.models import ColumnSchema, DatasetDetail, DatasetTableSummary

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = PROJECT_ROOT / "datasets" / "uploads"
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB limit

REJECTED_EXTENSIONS = {
    ".exe", ".sh", ".py", ".js", ".bat", ".cmd", ".ps1", ".vbs", ".dll", ".so",
    ".dylib", ".jar", ".war", ".php", ".rb", ".pl", ".bin", ".elf", ".c", ".cpp"
}
ALLOWED_EXTENSIONS = {".csv", ".parquet", ".zip"}


class DatasetUploadError(Exception):
    """Base exception for dataset upload validation failures."""
    pass


def normalize_table_name(filename: str) -> str:
    """Derive table name from file basename without extension, normalized to snake_case."""
    stem = Path(filename).stem
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", stem)
    clean = re.sub(r"_+", "_", clean).strip("_").lower()
    return clean or "table_data"


class DatasetUploadHandler:
    """Security-focused upload handler for user dataset files."""

    @classmethod
    def process_upload(
        cls,
        file_obj: BinaryIO,
        filename: str,
        display_name: str | None = None,
        description: str | None = None,
    ) -> DatasetDetail:
        """Process, validate, convert, and register uploaded CSV/Parquet/ZIP dataset."""
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise DatasetUploadError(
                f"Unsupported upload extension '{ext}'. Allowed formats: .csv, .parquet, .zip"
            )

        # Generate unique dataset_id
        unique_suffix = uuid.uuid4().hex[:8]
        clean_base = normalize_table_name(filename)
        dataset_id = f"upload_{clean_base}_{unique_suffix}"
        target_dir = UPLOADS_DIR / dataset_id
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Save uploaded bytes & enforce size limit
            temp_file = target_dir / f"raw_upload{ext}"
            size = 0
            with open(temp_file, "wb") as out:
                while chunk := file_obj.read(8192):
                    size += len(chunk)
                    if size > MAX_UPLOAD_SIZE:
                        raise DatasetUploadError(
                            f"Upload exceeds maximum allowed size limit of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB."
                        )
                    out.write(chunk)

            # 2. Process file based on extension
            data_files: list[Path] = []
            if ext == ".zip":
                data_files = cls._extract_and_validate_zip(temp_file, target_dir)
            elif ext in [".csv", ".parquet"]:
                dest_file = target_dir / f"{clean_base}{ext}"
                shutil.move(str(temp_file), str(dest_file))
                data_files = [dest_file]

            # 3. Detect and resolve table names + check collisions
            table_file_map: dict[str, Path] = {}
            for path in data_files:
                t_name = normalize_table_name(path.name)
                if t_name in table_file_map:
                    raise DatasetUploadError(
                        f"TABLE_NAME_COLLISION: Multiple uploaded files resolve to the table name '{t_name}' ({table_file_map[t_name].name} vs {path.name}). Table names must be unique."
                    )
                table_file_map[t_name] = path

            # 4. Convert all files into Parquet & compute schema using DuckDB
            con = duckdb.connect(":memory:")
            try:
                table_summaries: list[DatasetTableSummary] = []
                file_names: dict[str, str] = {}
                row_counts: dict[str, int] = {}

                for t_name, path in table_file_map.items():
                    parquet_dest = target_dir / f"{t_name}.parquet"

                    if path.suffix.lower() == ".parquet" and path != parquet_dest:
                        shutil.copy(str(path), str(parquet_dest))
                    elif path.suffix.lower() == ".csv":
                        con.execute(f"COPY (SELECT * FROM read_csv_auto('{path}')) TO '{parquet_dest}' (FORMAT PARQUET)")

                    # Inspect generated parquet
                    r_cnt = con.execute(f"SELECT COUNT(*) FROM read_parquet('{parquet_dest}')").fetchone()[0]
                    cols_info = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet_dest}')").fetchall()

                    cols = [
                        ColumnSchema(
                            name=col[0],
                            data_type=col[1],
                            nullable=col[2] == "YES",
                            ordinal_position=idx,
                        )
                        for idx, col in enumerate(cols_info, start=1)
                    ]

                    table_summaries.append(
                        DatasetTableSummary(
                            table_name=t_name,
                            row_count=r_cnt,
                            columns=cols,
                        )
                    )
                    file_names[t_name] = f"{t_name}.parquet"
                    row_counts[t_name] = r_cnt

                # 5. Compute content hash & generate manifest
                content_str = f"{dataset_id}:{json.dumps(row_counts)}:{json.dumps([t.model_dump() for t in table_summaries])}"
                d_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

                manifest_data = {
                    "dataset_id": dataset_id,
                    "display_name": display_name or clean_base.replace("_", " ").title(),
                    "description": description or f"Uploaded dataset from {filename}",
                    "source": "upload",
                    "profile": "custom",
                    "row_count_total": sum(row_counts.values()),
                    "table_count": len(table_summaries),
                    "size_bytes": size,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "dataset_hash": d_hash,
                    "schema_version": "1.0",
                    "is_builtin": False,
                    "is_upload": True,
                    "status": "READY",
                    "tags": ["uploaded", "custom"],
                    "file_names": file_names,
                    "row_counts": row_counts,
                    "table_summaries": [t.model_dump() for t in table_summaries],
                }

                manifest_file = target_dir / "manifest.json"
                with open(manifest_file, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=2)

                return DatasetDetail(
                    dataset_id=dataset_id,
                    display_name=manifest_data["display_name"],
                    description=manifest_data["description"],
                    source="upload",
                    profile="custom",
                    row_count_total=manifest_data["row_count_total"],
                    table_count=len(table_summaries),
                    size_bytes=size,
                    created_at=manifest_data["created_at"],
                    dataset_hash=d_hash,
                    schema_version="1.0",
                    is_builtin=False,
                    is_upload=True,
                    status="READY",
                    tags=["uploaded", "custom"],
                    table_summaries=table_summaries,
                    manifest_path=str(manifest_file),
                )
            finally:
                con.close()

        except Exception as exc:
            # Clean up target directory on failure
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            if isinstance(exc, DatasetUploadError):
                raise
            raise DatasetUploadError(f"Failed to process uploaded dataset: {exc}") from exc

    @classmethod
    def _extract_and_validate_zip(cls, zip_path: Path, target_dir: Path) -> list[Path]:
        """Extract ZIP archive with strict Zip-Slip protection and executable rejection."""
        extracted_files: list[Path] = []
        canonical_target = target_dir.resolve()

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for member in zip_ref.infolist():
                # Ignore directories
                if member.is_dir():
                    continue

                # Check Zip-Slip path traversal
                dest_path = (target_dir / member.filename).resolve()
                if not str(dest_path).startswith(str(canonical_target)):
                    raise DatasetUploadError(
                        f"ZIP_SLIP_ATTACK_REJECTED: Zip member path '{member.filename}' attempts directory traversal outside target path."
                    )

                # Check executable file extensions
                member_ext = Path(member.filename).suffix.lower()
                if member_ext in REJECTED_EXTENSIONS:
                    raise DatasetUploadError(
                        f"EXECUTABLE_FILE_REJECTED: Executable file extension '{member_ext}' is not permitted inside upload archives."
                    )

                if member_ext in [".csv", ".parquet"]:
                    # Flatten filename to target_dir directly
                    clean_name = Path(member.filename).name
                    extracted_dest = target_dir / clean_name

                    with zip_ref.open(member) as source, open(extracted_dest, "wb") as target:
                        shutil.copyfileobj(source, target)

                    extracted_files.append(extracted_dest)

        if not extracted_files:
            raise DatasetUploadError(
                "ZIP archive contains no valid .csv or .parquet files."
            )

        return extracted_files
