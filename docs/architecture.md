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

## Current Architecture (Phase 0 – Phase 7)

```
┌────────────┐      ┌────────────────┐      ┌────────────┐
│  Frontend  │─────▶│  FastAPI       │─────▶│ PostgreSQL │
│  React/TS  │      │  Backend       │      │ (Audit Log)│
└────────────┘      │                │      └────────────┘
                    │  analyzer/     │
                    │  lab/          │      ┌────────────┐
                    │  execution/    │─────▶│ DuckDB     │
                    │  validation/   │      │ (Parquet)  │
                    │  diagnosis/    │      └────────────┘
                    │  translator/   │
                    │  diagnosis_ai/ │      ┌────────────┐
                    │   context      │─────▶│ Generative │
                    │   prompts      │      │ LLM (AI)   │
                    │   evidence     │      └────────────┘
                    │   scope        │
                    └────────────────┘
```

## Phase Progression

1. **Phase 0**: Architecture & Domain Foundations
2. **Phase 1**: Static Analysis Engine (SQLGlot AST parsing & normalization)
3. **Phase 2**: Synthetic Data & Scenario Generator Engine
4. **Phase 3**: Multi-Dialect Query Execution & Artifact Storage (DuckDB Engine)
5. **Phase 4**: Multi-Layer Validation Engine (Deterministic semantic equivalence checking)
6. **Phase 5**: Discrepancy Classification & Evidence Consolidation
7. **Phase 6**: AI-Assisted SQL Translation Engine
8. **Phase 7**: AI-Grounded Discrepancy Diagnosis & Repair Proposal Engine (`PROPOSED` candidates only)

## Services & Modules

| Module / Service   | Technology          | Purpose                                                     |
|--------------------|---------------------|-------------------------------------------------------------|
| backend.analyzer   | Python / SQLGlot    | Deterministic SQL parsing, extraction, AST diff            |
| backend.lab        | Python / Pandas     | Synthetic dataset & 20 benchmark scenario lab              |
| backend.execution  | Python / DuckDB     | Read-only isolated execution engine & Parquet artifacts     |
| backend.validation | Python              | Independent semantic validation (schema, rows, aggregates, rules, edge cases) |
| backend.diagnosis  | Python              | Discrepancy classification & evidence consolidation (11 categories) |
| backend.translator | Python / OpenAI SDK | AI-assisted SQL translation candidate generation & prompt engineering |
| backend            | Python / FastAPI    | API endpoints                                               |
| postgres           | PostgreSQL 16       | Audit records (`executions`, `validations`, `diagnoses`, `translations`) |
