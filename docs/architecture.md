# MIGRA-Q Architecture

## Overview

MIGRA-Q verifies whether migrated SQL logic preserves the source behavior.
AI may generate a target SQL migration, but MIGRA-Q independently validates it.

## Core Principle

```
Deterministic Core:          LLM / AI (later phases):
  - SQL parsing (SQLGlot)      - translation
  - AST normalization           - explanation
  - rule extraction             - repair proposal
  - synthetic lab & benchmarks
  - execution engine (DuckDB)
  - semantic validation engine
  - structural comparison
  - execution & validation
  - assurance gating
```

## Current Architecture (Phase 0 + Phase 1 + Phase 2 + Phase 3 + Phase 4)

```
┌────────────┐      ┌────────────────┐      ┌────────────┐
│  Frontend   │─────▶│  FastAPI        │─────▶│ PostgreSQL │
│  React/TS   │      │  Backend        │      │ (Audit Log)│
└────────────┘      │                │      └────────────┘
                     │  analyzer/     │
                     │  lab/          │      ┌────────────┐
                     │  execution/    │─────▶│ DuckDB     │
                     │  validation/   │      │ (Parquet)  │
                     │   orchestrator │      └────────────┘
                     │   validators   │
                     └────────────────┘
```

## Services & Modules

| Module / Service   | Technology          | Purpose                                                     |
|--------------------|---------------------|-------------------------------------------------------------|
| backend.analyzer   | Python / SQLGlot    | Deterministic SQL parsing, extraction, AST diff            |
| backend.lab        | Python / Pandas     | Synthetic dataset & 20 benchmark scenario lab              |
| backend.execution  | Python / DuckDB     | Read-only isolated execution engine & Parquet artifacts     |
| backend.validation | Python              | Independent semantic validation (schema, rows, aggregates, rules, edge cases) |
| backend            | Python / FastAPI    | API endpoints                                               |
| postgres           | PostgreSQL 16       | Audit records (`executions`, `validations`, `validation_results` tables) |
