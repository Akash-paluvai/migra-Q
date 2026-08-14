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
  - structural comparison
  - execution & validation
  - assurance gating
```

## Current Architecture (Phase 0 + 1)

```
┌────────────┐      ┌────────────────┐      ┌────────────┐
│  Frontend   │─────▶│  FastAPI        │─────▶│ PostgreSQL │
│  React/TS   │      │  Backend        │      │            │
└────────────┘      │                │      └────────────┘
                     │  analyzer/     │
                     │   parser       │      ┌────────────┐
                     │   normalizer   │      │ DuckDB     │
                     │   extractor    │      │ (embedded) │
                     │   diff         │      └────────────┘
                     └────────────────┘
```

## Services

| Service    | Technology          | Purpose                    |
|------------|---------------------|----------------------------|
| backend    | Python / FastAPI    | API, SQL analysis          |
| frontend   | React / Vite / TS   | Minimal status UI          |
| postgres   | PostgreSQL 16       | Persistent storage         |
| duckdb     | Embedded library    | Future: migration sandbox  |
