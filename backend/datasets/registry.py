"""Phase 10.1 Dataset Registry.

Authoritative manager for built-in benchmark datasets and uploaded user datasets.
Ensures every registered dataset points to real manifests and physical Parquet files.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from backend.core.logging import get_logger
from backend.datasets.models import (
    ColumnSchema,
    DatasetDetail,
    DatasetPreviewResponse,
    DatasetSummary,
    DatasetTableSummary,
)

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASETS_DIR = PROJECT_ROOT / "datasets" / "generated"
UPLOADS_DIR = PROJECT_ROOT / "datasets" / "uploads"


class DatasetRegistry:
    """Registry maintaining authoritative built-in and user-uploaded dataset metadata."""

    def __init__(self) -> None:
        DATASETS_DIR.mkdir(parents=True, exist_ok=True)
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        self._custom_datasets: dict[str, DatasetDetail] = {}
        self._ensure_builtin_datasets()

    def list_datasets(self) -> list[DatasetSummary]:
        """List all available datasets (built-in + uploaded)."""
        summaries: list[DatasetSummary] = []
        for dataset_dir in self._get_all_dataset_dirs():
            manifest_file = dataset_dir / "manifest.json"
            if manifest_file.exists():
                summary = self._load_summary_from_manifest(dataset_dir, manifest_file)
                if summary:
                    summaries.append(summary)

        # Include custom datasets in memory if any
        for d_id, detail in self._custom_datasets.items():
            if not any(s.dataset_id == d_id for s in summaries):
                summaries.append(detail)

        return summaries

    def get_dataset(self, dataset_id: str) -> DatasetDetail | None:
        """Retrieve detailed dataset specification including table schemas."""
        if dataset_id in self._custom_datasets:
            return self._custom_datasets[dataset_id]

        dataset_dir = self._resolve_dataset_dir(dataset_id)
        if not dataset_dir:
            return None

        manifest_file = dataset_dir / "manifest.json"
        if not manifest_file.exists():
            return None

        return self._load_detail_from_manifest(dataset_dir, manifest_file)

    def exists(self, dataset_id: str) -> bool:
        """Check if dataset ID exists in registry."""
        return self.get_dataset(dataset_id) is not None

    def resolve_schema(self, dataset_id: str) -> list[DatasetTableSummary]:
        """Inspect and return table column schemas for a dataset using DuckDB."""
        detail = self.get_dataset(dataset_id)
        if not detail:
            return []
        return detail.table_summaries

    def resolve_preview(
        self,
        dataset_id: str,
        table_name: str | None = None,
        limit: int = 100,
    ) -> DatasetPreviewResponse:
        """Fetch sample row preview for a dataset table (max limit 100 rows)."""
        bounded_limit = min(max(1, limit), 100)
        detail = self.get_dataset(dataset_id)
        if not detail or not detail.table_summaries:
            return DatasetPreviewResponse(
                dataset_id=dataset_id,
                table_name=table_name or "",
                total_rows=0,
                returned_rows=0,
                columns=[],
                rows=[],
            )

        # Default to first table if unspecified
        target_table = table_name or detail.table_summaries[0].table_name
        table_summary = next(
            (t for t in detail.table_summaries if t.table_name.lower() == target_table.lower()),
            detail.table_summaries[0],
        )

        dataset_dir = self._resolve_dataset_dir(dataset_id)
        if not dataset_dir:
            return DatasetPreviewResponse(
                dataset_id=dataset_id,
                table_name=target_table,
                total_rows=table_summary.row_count,
                returned_rows=0,
                columns=table_summary.columns,
                rows=[],
            )

        # Locate parquet/csv file for table
        file_path = None
        for ext in [".parquet", ".csv"]:
            candidate = dataset_dir / f"{table_summary.table_name}{ext}"
            if candidate.exists():
                file_path = candidate
                break

        if not file_path:
            return DatasetPreviewResponse(
                dataset_id=dataset_id,
                table_name=target_table,
                total_rows=table_summary.row_count,
                returned_rows=0,
                columns=table_summary.columns,
                rows=[],
            )

        con = duckdb.connect(":memory:")
        try:
            if file_path.suffix == ".parquet":
                query = f"SELECT * FROM read_parquet('{file_path}') LIMIT {bounded_limit}"
            else:
                query = f"SELECT * FROM read_csv_auto('{file_path}') LIMIT {bounded_limit}"

            df = con.execute(query).fetchdf()
            # Replace NaNs with None for clean JSON serialization
            df = df.where(df.notnull(), None)
            rows = df.to_dict(orient="records")

            return DatasetPreviewResponse(
                dataset_id=dataset_id,
                table_name=table_summary.table_name,
                total_rows=table_summary.row_count,
                returned_rows=len(rows),
                columns=table_summary.columns,
                rows=rows,
            )
        except Exception as exc:
            logger.error(f"Failed to preview table {target_table} in {dataset_id}: {exc}")
            return DatasetPreviewResponse(
                dataset_id=dataset_id,
                table_name=target_table,
                total_rows=table_summary.row_count,
                returned_rows=0,
                columns=table_summary.columns,
                rows=[],
            )
        finally:
            con.close()

    def register_dataset(self, dataset: DatasetDetail) -> None:
        """Register a new custom or uploaded dataset detail."""
        self._custom_datasets[dataset.dataset_id] = dataset

    # -----------------------------------------------------------------------
    # Built-in Dataset Seeding
    # -----------------------------------------------------------------------

    def _ensure_builtin_datasets(self) -> None:
        """Ensure all 6 built-in datasets exist physically on disk."""
        builtin_specs = [
            ("customer_risk", "Customer Risk Benchmark", "CASE statements and threshold boundary condition benchmarks", ["boundary", "case", "benchmark"]),
            ("customer_aggregation", "Aggregation & Metrics Lab", "GROUP BY, SUM, COUNT, and AVG aggregation benchmarks", ["aggregation", "group_by"]),
            ("null_semantics", "Null Semantics & Coalesce Lab", "NULL comparison, COALESCE, and IS NULL filtering benchmarks", ["nulls", "coalesce"]),
            ("join_semantics", "Join & Cardinality Lab", "INNER vs LEFT JOIN and duplicate key cardinality benchmarks", ["join", "cardinality"]),
            ("date_semantics", "Date & Timestamp Lab", "Date boundaries, truncations, and timestamp extraction benchmarks", ["date", "timestamp"]),
            ("mixed_business_logic", "Enterprise Multi-Rule Analytics", "Complex multi-rule enterprise analytics with mixed logic", ["enterprise", "mixed"]),
            ("enterprise_metrics", "Enterprise Metrics Benchmark", "Enterprise KPI and metrics benchmark with 5000 rows", ["enterprise", "metrics"]),
        ]

        for dataset_id, name, desc, tags in builtin_specs:
            target_dir = DATASETS_DIR / dataset_id
            manifest_file = target_dir / "manifest.json"
            if not manifest_file.exists():
                self._seed_builtin_dataset(dataset_id, name, desc, tags, target_dir)

    def _seed_builtin_dataset(
        self,
        dataset_id: str,
        name: str,
        desc: str,
        tags: list[str],
        target_dir: Path,
    ) -> None:
        """Generate distinct Parquet tables for a built-in dataset."""
        target_dir.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect(":memory:")

        try:
            if dataset_id == "customer_risk":
                con.execute("CREATE TABLE customers AS SELECT i AS customer_id, 'SEG_' || (i % 5) AS customer_segment FROM range(1, 5001) t(i)")
                con.execute("CREATE TABLE accounts AS SELECT i AS account_id, (i % 5000) + 1 AS customer_id, (i * 15.5) AS balance FROM range(1, 10001) t(i)")
                con.execute("CREATE TABLE transactions AS SELECT i AS transaction_id, (i % 5000) + 1 AS customer_id, CASE WHEN i % 2 = 0 THEN 500.0 ELSE (i % 1000) * 1.5 END AS amount, 'COMPLETED' AS status, CURRENT_TIMESTAMP AS timestamp FROM range(1, 10001) t(i)")
                con.execute("CREATE TABLE support_cases AS SELECT i AS case_id, (i % 5000) + 1 AS customer_id, 'OPEN' AS status FROM range(1, 1001) t(i)")
            elif dataset_id == "customer_aggregation":
                con.execute("CREATE TABLE sales_region AS SELECT i AS region_id, 'Region_' || (i % 10) AS region_name FROM range(1, 101) t(i)")
                con.execute("CREATE TABLE monthly_sales AS SELECT i AS sale_id, (i % 10) + 1 AS region_id, (i * 25.0) AS revenue, (i % 12) + 1 AS sale_month, 2026 AS sale_year FROM range(1, 5001) t(i)")
            elif dataset_id == "null_semantics":
                con.execute("CREATE TABLE product_catalog AS SELECT i AS product_id, 'Prod_' || i AS product_name, CASE WHEN i % 3 = 0 THEN NULL ELSE i * 10.0 END AS list_price, CASE WHEN i % 5 = 0 THEN NULL ELSE 'Active' END AS status FROM range(1, 3001) t(i)")
                con.execute("CREATE TABLE inventory_levels AS SELECT i AS item_id, (i % 3000) + 1 AS product_id, CASE WHEN i % 4 = 0 THEN NULL ELSE (i % 50) END AS stock_qty FROM range(1, 3001) t(i)")
            elif dataset_id == "join_semantics":
                con.execute("CREATE TABLE primary_entity AS SELECT i AS entity_id, 'Code_' || (i % 50) AS ref_code, i * 100 AS base_val FROM range(1, 2001) t(i)")
                con.execute("CREATE TABLE secondary_entity AS SELECT i AS detail_id, (i % 1500) + 1 AS entity_id, 'Code_' || (i % 50) AS ref_code, (i % 10) * 5.5 AS secondary_val FROM range(1, 4001) t(i)")
            elif dataset_id == "date_semantics":
                con.execute("CREATE TABLE event_logs AS SELECT i AS event_id, DATE '2026-01-01' + INTERVAL (i % 365) DAY AS event_date, TIMESTAMP '2026-01-01 08:00:00' + INTERVAL (i % 86400) SECOND AS event_time, 'USER_' || (i % 100) AS user_id FROM range(1, 4001) t(i)")
            else:  # mixed_business_logic or enterprise_metrics
                con.execute("CREATE TABLE enterprise_metrics AS SELECT i AS metric_id, 'Dept_' || (i % 8) AS department, i * 12.5 AS score, CASE WHEN i % 2 = 0 THEN 'PASS' ELSE 'FAIL' END AS gate_status FROM range(1, 5001) t(i)")

            tables = con.execute("SHOW TABLES").fetchall()
            file_names = {}
            row_counts = {}
            table_schemas = []

            for (t_name,) in tables:
                p_path = target_dir / f"{t_name}.parquet"
                con.execute(f"COPY {t_name} TO '{p_path}' (FORMAT PARQUET)")
                r_cnt = con.execute(f"SELECT COUNT(*) FROM {t_name}").fetchone()[0]
                file_names[t_name] = f"{t_name}.parquet"
                row_counts[t_name] = r_cnt

                # Describe columns
                cols_info = con.execute(f"DESCRIBE {t_name}").fetchall()
                cols = []
                for idx, col in enumerate(cols_info, start=1):
                    cols.append(
                        ColumnSchema(
                            name=col[0],
                            data_type=col[1],
                            nullable=col[2] == "YES",
                            ordinal_position=idx,
                        )
                    )
                table_schemas.append(
                    DatasetTableSummary(
                        table_name=t_name,
                        row_count=r_cnt,
                        columns=cols,
                    )
                )

            # Compute distinct dataset hash
            content_str = f"{dataset_id}:{json.dumps(row_counts)}:{json.dumps([t.model_dump() for t in table_schemas])}"
            d_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

            manifest_data = {
                "dataset_id": dataset_id,
                "display_name": name,
                "description": desc,
                "source": "builtin",
                "profile": "dev",
                "row_count_total": sum(row_counts.values()),
                "table_count": len(table_schemas),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "dataset_hash": d_hash,
                "schema_version": "1.0",
                "is_builtin": True,
                "is_upload": False,
                "tags": tags,
                "file_names": file_names,
                "row_counts": row_counts,
                "table_summaries": [t.model_dump() for t in table_schemas],
            }

            with open(target_dir / "manifest.json", "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)

        except Exception as exc:
            logger.error(f"Failed to seed built-in dataset {dataset_id}: {exc}")
        finally:
            con.close()

    # -----------------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------------

    def _get_all_dataset_dirs(self) -> list[Path]:
        """Find all dataset directories in generated and upload paths."""
        dirs = []
        if DATASETS_DIR.exists():
            dirs.extend([d for d in DATASETS_DIR.iterdir() if d.is_dir()])
        if UPLOADS_DIR.exists():
            dirs.extend([d for d in UPLOADS_DIR.iterdir() if d.is_dir()])
        return dirs

    def _resolve_dataset_dir(self, dataset_id: str) -> Path | None:
        """Locate dataset directory on disk."""
        candidate_gen = DATASETS_DIR / dataset_id
        if candidate_gen.exists():
            return candidate_gen
        candidate_up = UPLOADS_DIR / dataset_id
        if candidate_up.exists():
            return candidate_up
        return None

    def _load_summary_from_manifest(
        self, dataset_dir: Path, manifest_file: Path
    ) -> DatasetSummary | None:
        """Load lightweight summary from manifest."""
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            dataset_id = data.get("dataset_id", dataset_dir.name)
            row_counts = data.get("row_counts", {})
            total_rows = data.get("row_count_total", sum(row_counts.values()) if row_counts else 0)

            # Compute hash if missing
            d_hash = data.get("dataset_hash")
            if not d_hash or d_hash == "hash-unknown":
                content_str = f"{dataset_id}:{json.dumps(row_counts)}"
                d_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

            return DatasetSummary(
                dataset_id=dataset_id,
                display_name=data.get("display_name", dataset_id.replace("_", " ").title()),
                description=data.get("description", f"Dataset {dataset_id}"),
                source=data.get("source", "synthetic"),
                profile=data.get("profile", "dev"),
                row_count_total=total_rows,
                table_count=data.get("table_count", len(row_counts) or 1),
                size_bytes=data.get("size_bytes", 0),
                created_at=data.get("created_at", data.get("generation_timestamp", datetime.now(timezone.utc).isoformat())),
                dataset_hash=d_hash,
                schema_version=data.get("schema_version", "1.0"),
                is_builtin=data.get("is_builtin", True),
                is_upload=data.get("is_upload", False),
                status=data.get("status", "READY"),
                tags=data.get("tags", []),
            )
        except Exception as exc:
            logger.error(f"Failed to load manifest summary from {manifest_file}: {exc}")
            return None

    def _load_detail_from_manifest(
        self, dataset_dir: Path, manifest_file: Path
    ) -> DatasetDetail | None:
        """Load full detail from manifest."""
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            dataset_id = data.get("dataset_id", dataset_dir.name)
            raw_tables = data.get("table_summaries", [])
            table_summaries: list[DatasetTableSummary] = []

            if raw_tables:
                table_summaries = [DatasetTableSummary.model_validate(t) for t in raw_tables]
            elif "table_schemas" in data and isinstance(data["table_schemas"], dict):
                row_counts = data.get("row_counts", {})
                for t_name, t_info in data["table_schemas"].items():
                    cols = [
                        ColumnSchema(
                            name=c.get("name", ""),
                            data_type=c.get("data_type", "string"),
                            nullable=c.get("nullable", True),
                            ordinal_position=idx,
                            primary_key=c.get("name") in t_info.get("primary_key", []),
                        )
                        for idx, c in enumerate(t_info.get("columns", []), start=1)
                    ]
                    table_summaries.append(
                        DatasetTableSummary(
                            table_name=t_name,
                            row_count=row_counts.get(t_name, 0),
                            columns=cols,
                        )
                    )

            row_counts = data.get("row_counts", {})
            total_rows = data.get("row_count_total", sum(row_counts.values()) if row_counts else sum(t.row_count for t in table_summaries))

            d_hash = data.get("dataset_hash")
            if not d_hash or d_hash == "hash-unknown":
                content_str = f"{dataset_id}:{json.dumps(row_counts)}:{json.dumps([t.model_dump() for t in table_summaries])}"
                d_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

            return DatasetDetail(
                dataset_id=dataset_id,
                display_name=data.get("display_name", dataset_id.replace("_", " ").title()),
                description=data.get("description", f"Dataset {dataset_id}"),
                source=data.get("source", "synthetic"),
                profile=data.get("profile", "dev"),
                row_count_total=total_rows,
                table_count=len(table_summaries),
                size_bytes=data.get("size_bytes", 0),
                created_at=data.get("created_at", data.get("generation_timestamp", datetime.now(timezone.utc).isoformat())),
                dataset_hash=d_hash,
                schema_version=data.get("schema_version", "1.0"),
                is_builtin=data.get("is_builtin", True),
                is_upload=data.get("is_upload", False),
                status=data.get("status", "READY"),
                tags=data.get("tags", []),
                table_summaries=table_summaries,
                manifest_path=str(manifest_file),
            )
        except Exception as exc:
            logger.error(f"Failed to load manifest detail from {manifest_file}: {exc}")
            return None
