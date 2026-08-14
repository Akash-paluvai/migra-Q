# Phase 3 — Deterministic SQL Execution Engine

## 1. Overview

Phase 3 establishes the **objective truth mechanism** for MIGRA-Q. Given a source or target SQL query and a Phase 2 synthetic dataset, the execution engine runs the query inside an isolated, in-memory DuckDB sandbox and captures reproducible execution artifacts.

The engine answers strictly:
- Did the SQL execute successfully?
- What schema did it produce?
- How many rows did it produce?
- What result sample and Parquet artifact were generated?
- How long did execution take?
- If execution failed, what was the categorized error?

> [!IMPORTANT]
> The Execution Engine does **NOT** calculate semantic equivalence, classify migration discrepancies, or invoke AI models. Those responsibilities are explicitly deferred to Phase 4+.

---

## 2. Execution Architecture

```
API / CLI Request
      │
      ▼
ExecutionService
      │
      ├──▶ 1. Validate read-only security policy (SQLGlot AST)
      ├──▶ 2. Resolve dataset (Phase 2 manifest.json)
      ├──▶ 3. Calculate query_hash (SHA-256) & dataset_hash (SHA-256)
      │
      ▼
SandboxExecutor / DuckDBRunner
      │
      ├──▶ 4. Create in-memory DuckDB connection (duckdb.connect(":memory:"))
      ├──▶ 5. Mount Parquet files as read-only views (customers, accounts, transactions, support_cases)
      ├──▶ 6. Execute query under process/thread timeout boundary (default: 10s)
      │
      ▼
Result Capture Engine
      │
      ├──▶ 7. Export full result to datasets/runtime_results/{execution_id}/result.parquet
      ├──▶ 8. Save metadata to datasets/runtime_results/{execution_id}/metadata.json
      └──▶ 9. Persist audit record to PostgreSQL executions table
```

---

## 3. Security Guarantees & Read-Only Policy

1. **Read-Only Enforcement**: Submitted SQL queries are parsed using SQLGlot AST inspection. Statements containing `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `ALTER`, `COPY`, `INSTALL`, or `LOAD` are immediately rejected with `SECURITY_ERROR`.
2. **Credential Isolation**: PostgreSQL database credentials and application secrets are NEVER exposed to the DuckDB execution context.
3. **Dataset Protection**: Phase 2 source Parquet datasets are registered as read-only views and are NEVER mutated.
4. **Timeout Bounds**: Queries exceeding `EXECUTION_TIMEOUT_SECONDS = 10` are halted and return `status = TIMEOUT`.

---

## 4. Result Artifact Storage & Inlining Strategy

- **Canonical Format**: Apache Parquet (`result.parquet`).
- **Inline Bounding**: If total rows <= 500 (`MAX_INLINE_RESULT_ROWS`), representative sample rows are returned in the API/CLI response. Full row sets always remain stored in the Parquet artifact to avoid memory bloat.

---

## 5. API & CLI Reference

### CLI Usage

```bash
# Run a single query against a dataset
python -m backend.execution.cli run \
  --sql examples/execution/simple_customer_query.sql \
  --dataset dev

# Inspect execution metadata by execution_id
python -m backend.execution.cli inspect --execution-id <id>

# Run source and target candidates independently
python -m backend.execution.cli compare-inputs \
  --source examples/execution/customer_risk_source.sql \
  --target examples/execution/customer_risk_target.sql \
  --dataset dev
```

### API Endpoints

- `POST /api/v1/executions` — Submits a query execution request.
- `GET /api/v1/executions/{execution_id}` — Retrieves execution metadata.
