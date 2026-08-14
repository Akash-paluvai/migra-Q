"""Result capture engine — materializes results, captures schemas,
and persists Parquet artifacts.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb

from backend.execution.exceptions import ResultCaptureError
from backend.execution.models import ColumnSchema

MAX_INLINE_RESULT_ROWS = 500


def capture_and_persist_result(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    execution_id: str,
    query_hash: str,
    dataset_id: str,
    dataset_hash: str,
    duration_ms: float,
    base_results_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute query result capture and persist Parquet artifact.

    Returns dict of captured metadata including row_count, columns, sample_data, and artifact path.
    """
    if base_results_dir is None:
        base_results_dir = Path.cwd() / "datasets" / "runtime_results"

    exec_dir = base_results_dir / execution_id
    exec_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = exec_dir / "result.parquet"

    clean_sql = sql.strip().rstrip(";")
    try:
        # Create temp table in DuckDB to capture exact query output
        conn.execute(f"CREATE TEMP TABLE _exec_out AS ({clean_sql});")
    except Exception as exc:
        raise ResultCaptureError(f"Query execution failed: {exc}") from exc

    # 1. Capture exact total row count
    row_cnt_res = conn.execute("SELECT COUNT(*) FROM _exec_out;").fetchone()
    total_row_count = int(row_cnt_res[0]) if row_cnt_res else 0

    # 2. Capture schema (column names and types)
    schema_res = conn.execute("DESCRIBE _exec_out;").fetchall()
    columns = [ColumnSchema(name=row[0], type=str(row[1])) for row in schema_res]

    # 3. Export full result to Parquet artifact
    try:
        conn.execute(f"COPY _exec_out TO '{parquet_path.resolve()}' (FORMAT PARQUET);")
    except Exception as exc:
        raise ResultCaptureError(
            f"Failed to write Parquet artifact to {parquet_path}: {exc}"
        ) from exc

    # 4. Check if SQL contains ORDER BY clause
    has_order_by = "ORDER BY" in sql.upper()

    # 5. Extract bounded inline sample
    sample_data: list[dict[str, Any]] = []
    if total_row_count > 0:
        sample_rows = conn.execute(
            f"SELECT * FROM _exec_out LIMIT {MAX_INLINE_RESULT_ROWS};"
        ).fetchall()
        col_names = [col.name for col in columns]
        for row in sample_rows:
            row_dict = {}
            for col_name, val in zip(col_names, row):
                # Convert non-serializable objects (dates/timestamps/decimals) to strings/floats
                if isinstance(val, (datetime, datetime)):
                    row_dict[col_name] = val.isoformat()
                elif hasattr(val, "isoformat"):
                    row_dict[col_name] = val.isoformat()
                else:
                    row_dict[col_name] = val
            sample_data.append(row_dict)

    # 6. Save metadata.json
    metadata = {
        "execution_id": execution_id,
        "query_hash": query_hash,
        "dataset_id": dataset_id,
        "dataset_hash": dataset_hash,
        "engine": "duckdb",
        "engine_version": duckdb.__version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "status": "SUCCESS",
        "row_count": total_row_count,
        "columns": [c.model_dump() for c in columns],
        "sample_is_ordered": has_order_by,
        "result_artifact": str(parquet_path.relative_to(Path.cwd())),
    }

    metadata_path = exec_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "row_count": total_row_count,
        "columns": columns,
        "sample_data": sample_data,
        "sample_is_ordered": has_order_by,
        "result_artifact": str(parquet_path.relative_to(Path.cwd())),
    }
