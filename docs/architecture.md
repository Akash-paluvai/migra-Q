# MIGRA-Q Architecture

## Overview

MIGRA-Q verifies whether migrated SQL logic preserves source behavior.
AI may generate a target SQL migration candidate or repair proposal, but MIGRA-Q independently and deterministically validates it.

## Core Principle

```
Deterministic Core (Phases 1-5, Phase 8):      LLM / AI Gating (Phases 6-7):
  - SQL parsing (SQLGlot AST)                   - SQL translation candidates
  - AST normalization & rule extraction          - Grounded discrepancy diagnosis
  - Synthetic lab & 20 benchmark scenarios       - Repair proposal generation
  - DuckDB execution sandbox & Parquet artifacts
  - Multi-layer semantic validation
  - Discrepancy classification & evidence
  - Repair candidate integrity validation
  - Deterministic re-validation & proof chain
```

## Current Architecture (Phase 0 – Phase 8)

```
┌────────────┐      ┌─────────────────────────┐      ┌────────────┐
│  Frontend  │─────▶│  FastAPI Backend        │─────▶│ PostgreSQL │
│  React/TS  │      │                         │      │ (Audit Log)│
└────────────┘      │  analyzer/              │      └────────────┘
                    │  lab/                   │
                    │  execution/             │      ┌────────────┐
                    │  validation/            │─────▶│ DuckDB     │
                    │  diagnosis/             │      │ (Parquet)  │
                    │  translator/ (Phase 6)  │      └────────────┘
                    │  diagnosis_ai/ (Phase 7)│
                    │  repair_verification/   │      ┌────────────┐
                    │    candidate_validator  │─────▶│ Generative │
                    │    executor adapter     │      │ LLM (AI)   │
                    │    discrepancy_diff     │      └────────────┘
                    │    status_determiner    │
                    └─────────────────────────┘
```

## Phase Progression

1. **Phase 0**: Architecture & Domain Foundations
2. **Phase 1**: Static Analysis Engine (SQLGlot AST parsing & normalization)
3. **Phase 2**: Synthetic Data & Scenario Generator Engine
4. **Phase 3**: Multi-Dialect Query Execution & Artifact Storage (DuckDB Engine)
5. **Phase 4**: Multi-Layer Validation Engine (Deterministic semantic equivalence checking)
6. **Phase 5**: Discrepancy Classification & Evidence Consolidation
7. **Phase 6**: AI-Assisted SQL Translation Engine
8. **Phase 7**: AI-Grounded Discrepancy Diagnosis & Repair Proposal Engine
9. **Phase 8**: Repair Execution & Deterministic Re-Validation Engine (Deterministic candidate validation & formal proof chain)

## Services & Modules

| Module / Service | Technology | Purpose |
|---|---|---|
| `backend.analyzer` | Python / SQLGlot | Deterministic SQL parsing, extraction, AST diff |
| `backend.lab` | Python / Pandas | Synthetic dataset & 20 benchmark scenario lab |
| `backend.execution` | Python / DuckDB | Read-only isolated execution engine & Parquet artifacts |
| `backend.validation` | Python | Independent semantic validation (schema, rows, aggregates, rules, edge cases) |
| `backend.diagnosis` | Python | Discrepancy classification & evidence consolidation (11 categories) |
| `backend.translator` | Python / OpenAI SDK | AI-assisted SQL translation candidate generation |
| `backend.diagnosis_ai` | Python / OpenAI SDK | AI-grounded discrepancy diagnosis & repair proposal generation |
| `backend.repair_verification` | Python | Deterministic candidate integrity validation, DuckDB execution, re-validation & proof chain |
| `backend` | Python / FastAPI | REST API endpoints for all phases |
| `postgres` | PostgreSQL 16 | Audit records (`executions`, `validations`, `diagnoses`, `repair_verifications`, `repair_outcomes`) |
