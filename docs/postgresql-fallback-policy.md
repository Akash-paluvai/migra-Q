# PostgreSQL Fallback Policy

## 1. Overview
MIGRA-Q enforces an explicit PostgreSQL persistence policy across all operational environments.

## 2. Policy Requirements

1. **Mandatory Production/Development Engine**: PostgreSQL (`postgresql+psycopg://`) is the sole authorized relational database engine for `development`, `demo`, and `production` environments (`APP_ENV`).
2. **No Silent Fallbacks**: Under no circumstances will MIGRA-Q silently fall back to SQLite, local file-based databases, or unconfigured in-memory stores when PostgreSQL is unreachable.
3. **Explicit Failure Reporting**: If PostgreSQL is unreachable in `development`/`demo`/`production`:
   - System logs explicit connection error tracebacks.
   - `/api/v1/health` reports `"status": "degraded"` and `"database": "unavailable"`.
4. **Test Environment Isolation**: In-memory test repositories (`PERSISTENCE_MODE="memory"`) are strictly restricted to `APP_ENV="test"`. Attempting to set `PERSISTENCE_MODE="memory"` in non-test environments raises an immediate configuration `ValueError`.

## 3. Environment Configuration Matrix

| Environment (`APP_ENV`) | `PERSISTENCE_MODE` | Database Engine | Unreachable Action |
|---|---|---|---|
| `development` | `postgres` | PostgreSQL | Report Degraded (`/api/v1/health`), Log Error |
| `demo` | `postgres` | PostgreSQL | Report Degraded (`/api/v1/health`), Log Error |
| `production` | `postgres` | PostgreSQL | Report Degraded (`/api/v1/health`), Log Error |
| `test` | `memory` / `postgres` | In-Memory / Test DB | Isolated Test Runs |
