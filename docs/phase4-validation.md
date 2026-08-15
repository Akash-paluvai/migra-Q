# Phase 4 — Semantic Validation Engine

## 1. Purpose & Core Principles

Phase 4 is the **deterministic semantic validation layer** of MIGRA-Q.

It consumes:
1. **Source Execution Result** (Phase 3 artifact)
2. **Target Execution Result** (Phase 3 artifact)
3. **Source SQL Analysis** (Phase 1 AST abstraction)
4. **Target SQL Analysis** (Phase 1 AST abstraction)
5. **Benchmark Scenario / Dataset Manifest** (Phase 2 context)

And produces a structured `ValidationReport` containing independent `ValidationResult` objects.

> [!IMPORTANT]
> The Validation Engine operates as an **independent judge**. It does **NOT** invoke LLMs, perform automated repairs, or compute final production migration-assurance scores. Those responsibilities belong exclusively to Phase 5+.

---

## 2. Validation Architecture

```
               Phase 3
                  │
      ┌───────────┴───────────┐
      ▼                       ▼
Source Execution         Target Execution
      │                       │
      └───────────┬───────────┘
                  ▼
          Validation Engine
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
   Schema       Rows       Aggregates
      │           │           │
      └───────────┼───────────┘
                  ▼
          Business Rules
                  │
                  ▼
             Edge Cases
                  │
                  ▼
         ValidationReport
```

---

## 3. Validators Implemented

1. **SchemaValidator**: Compares column count, names, column ordering (configurable), normalized data types (e.g. `VARCHAR` <-> `STRING`), missing columns, and extra columns.
2. **RowValidator**: Performs primary key-based row comparison (`comparison_key`), groups duplicate keys, categorizes `MISSING_FROM_TARGET`, `EXTRA_IN_TARGET`, and value mismatches, and applies numeric tolerances (`abs_tol`, `rel_tol`).
3. **AggregateValidator**: Computes statistical aggregates (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `COUNT DISTINCT`) respecting SQL NULL semantics.
4. **BusinessRuleValidator**: Consumes Phase 1 `SQLAnalysis` AST abstractions to detect structural filter, join, aggregation, and CASE branch discrepancies.
5. **EdgeCaseValidator**: Tests adversarial Phase 2 benchmark scenarios (e.g., boundary values, NULL behavior) against result artifacts.

---

## 4. Evidence & Report Contracts

Every check returns a `ValidationResult` with structured `EvidenceItem` list:

```json
{
  "type": "VALUE_MISMATCH",
  "key": {
    "customer_id": "C18291"
  },
  "column": "risk_category",
  "source_value": "NORMAL",
  "target_value": "HIGH_RISK",
  "category": "VALUE_MISMATCH",
  "detail": "Column 'risk_category' mismatch for key {'customer_id': 'C18291'}."
}
```

Summary `overall_status` is an aggregate check status (`PASS`, `WARN`, `FAIL`, `ERROR`), and is **never** labeled as `APPROVED` or `PRODUCTION_READY`.

---

## 5. API & CLI Reference

### CLI Usage

```bash
# Run validation between source and target Phase 3 executions
python -m backend.validation.cli run \
  --source-execution <source_id> \
  --target-execution <target_id> \
  --comparison-key customer_id

# Inspect completed validation report
python -m backend.validation.cli inspect --validation-id <validation_id>
```

### API Endpoints

- `POST /api/v1/validations` — Execute semantic validation run.
- `GET /api/v1/validations/{validation_id}` — Retrieve completed validation report.

---

## 6. Reproducibility & Tolerance Policies

- **Numeric Tolerance**: Configurable `numeric_absolute_tolerance = 1e-6` and `numeric_relative_tolerance = 1e-5`.
- **NULL Semantics**: Explicitly handled (`NULL` == `NULL` is `True`, `NULL` == value is `False`).
- **Deterministic Evidence**: Representative evidence sampling (up to `max_evidence_items = 100`) is 100% deterministic across repeated runs.
