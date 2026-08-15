# Phase 5 — Discrepancy Classification & Evidence Consolidation Engine

## Overview

Phase 5 establishes the deterministic **Discrepancy Classification & Evidence Consolidation** engine for MIGRA-Q.

Phase 4 determines *whether* source and target SQL execution outputs differ across schema, row counts, cell values, aggregates, business rules, and edge cases.

Phase 5 answers:
1. **What TYPE** of semantic discrepancy occurred?
2. **WHERE** did it occur in the AST structure / query analysis?
3. **WHAT deterministic evidence** supports that classification?

Phase 5 is strictly non-diagnostic: it performs evidence-driven classification of observed behavioral differences, not LLM root-cause reasoning or AI code repair.

---

## Architecture & Data Flow

```
                      Phase 4 Validation Report
                                  │
                                  ▼
                        SignalExtractor
                                  │
                                  ▼
                       RawDiscrepancySignal[]
                                  │
                                  ▼
                        EvidenceConsolidator
                                  │
                        (Deduplication & Grouping
                         by Signature Hash)
                                  │
                                  ▼
                        DiscrepancyClassifier
                                  │
                   (Registry Priority Evaluation: 1..11)
                                  │
                                  ▼
                   Severity & Confidence Calculation
                                  │
                                  ▼
                        DiscrepancyRecord[]
                                  │
                                  ▼
                        DiscrepancyReport
                                  │
                 ┌────────────────┴────────────────┐
                 ▼                                 ▼
           PostgreSQL DB                    CLI & REST API
  (DiagnosisRecord, Discrepancies)        (format_discrepancy_summary)
```

---

## Core Discrepancy Taxonomy

Phase 5 categorizes all observed differences into 11 formal categories:

| Priority | Category | Enum Value | Description |
|---|---|---|---|
| 1 | Null Semantics | `NULL_SEMANTICS` | SQL NULL treatment differences (`IS NULL` vs `= NULL`, `COUNT(*)` vs `COUNT(col)`, `COALESCE`, `NVL`) |
| 2 | Boundary Condition | `BOUNDARY_CONDITION` | Off-by-one or inclusive vs exclusive boundary shifts (`>` vs `>=`, `<` vs `<=`, `BETWEEN`) |
| 3 | Join Semantics | `JOIN_SEMANTICS` | Join type or join condition changes (`INNER` vs `LEFT`, missing join predicates) |
| 4 | Aggregation Semantics | `AGGREGATION_SEMANTICS` | Function shifts, missing `DISTINCT`, or altered `GROUP BY` groupings |
| 5 | Date Semantics | `DATE_SEMANTICS` | Date/timestamp truncation, extraction, or interval calculation shifts (`DATE_TRUNC`, `EXTRACT`) |
| 6 | Type Conversion | `TYPE_CONVERSION` | Data type casting, overflow, rounding, or implicit type conversion differences |
| 7 | Case Logic | `CASE_LOGIC` | `CASE WHEN` branch condition changes, missing branches, or default `ELSE` shifts |
| 8 | Filter Logic | `FILTER_LOGIC` | Added, missing, or altered `WHERE` or `HAVING` predicate filters |
| 9 | Column Mapping | `COLUMN_MAPPING` | Column alias renames, position shifts, or expression-to-column assignment changes |
| 10 | Set Semantics | `SET_SEMANTICS` | Set operation changes (`UNION` vs `UNION ALL`, `INTERSECT`, `EXCEPT`) |
| 11 | Unknown | `UNKNOWN` | Fallback classification for differences without explicit rule matches |

---

## Deterministic Signature & Deduplication

Every discrepancy is assigned a SHA256 signature calculated from:

```text
signature_str = f"{category}:{analysis_path}:{normalized_source_expression}:{normalized_target_expression}"
discrepancy_signature = sha256(signature_str).hexdigest()[:16]
```

Expressions are normalized by:
1. Stripping outer whitespace.
2. Converting uppercase keywords.
3. Collapsing multiple spaces into single spaces.
4. Sorting comma-separated list tokens deterministically.

---

## Priority Rule Classifiers

Classifiers are evaluated in strict priority order (Rank 1 to Rank 11). The first matching classifier handles the signal:

1. **`NullSemanticsClassifier`**: Precedes all others when `COUNT(*)` vs `COUNT(col)` or `NULL` expressions are involved.
2. **`BoundaryClassifier`**: Matches inclusion operator shifts (`>` vs `>=`, `<` vs `<=`, `BETWEEN`).
3. **`JoinSemanticsClassifier`**: Matches `INNER` vs `LEFT`/`RIGHT` join shifts and join predicate changes.
4. **`AggregationClassifier`**: Matches function alterations (`SUM` vs `AVG`, `DISTINCT`).
5. **`DateSemanticsClassifier`**: Matches timestamp/date function shifts (`DATE_TRUNC`, `EXTRACT`).
6. **`TypeConversionClassifier`**: Matches `CAST`, `CONVERT`, or data type mismatches.
7. **`CaseLogicClassifier`**: Matches `CASE WHEN` condition or branch differences.
8. **`FilterLogicClassifier`**: Matches `WHERE`/`HAVING` filter additions/deletions.
9. **`ColumnMappingClassifier`**: Matches column alias or position shifts.
10. **`SetSemanticsClassifier`**: Matches set operation shifts.
11. **`GenericClassifier`**: Catch-all fallback (`UNKNOWN`).

---

## Deterministic Confidence Methodology

Confidence scores are assigned strictly based on empirical evidence strength:

- **0.85**: Structural AST diff evidence only (`BusinessRuleValidator` / `AST_ANALYZER`).
- **0.90**: Execution output evidence only (`RowValidator` / `SchemaValidator`).
- **0.95**: Combined Structural AST + Execution output evidence.
- **1.00**: Combined Structural AST + Execution output + Edge-Case boundary confirmation.
- **0.50**: Fallback for `UNKNOWN` category discrepancies.

---

## Severity Calculation Matrix

Severity is calculated deterministically from category criticality and affected output row percentage:

$$\text{Affected Percentage} = \frac{\text{Affected Row Count}}{\text{Total Output Rows}} \times 100$$

| Affected Row % | Critical Category (`NULL`, `JOIN`, `BOUNDARY`) | Standard Category (`FILTER`, `TYPE`, `CASE`) |
|---|---|---|
| $0\%$ (Structural only) | `LOW` | `INFO` / `LOW` |
| $> 0\%$ and $< 1\%$ | `MEDIUM` | `LOW` |
| $\ge 1\%$ and $< 20\%$ | `HIGH` | `MEDIUM` |
| $\ge 20\%$ | `CRITICAL` | `HIGH` |

---

## Persistence & REST API

### Database Tables
1. **`diagnoses`**: Primary record containing `diagnosis_id`, `validation_id`, `total_discrepancies`, `critical_count`, `high_count`, `medium_count`, `low_count`, `info_count`, `overall_confidence`.
2. **`discrepancies`**: Individual records containing `discrepancy_id`, `category`, `subcategory`, `severity`, `confidence`, `source_expression`, `target_expression`, `analysis_path`, `affected_row_count`, `discrepancy_signature`.
3. **`discrepancy_evidence`**: Bounded evidence items referencing specific columns, values, row keys, and validator checks.

### API Endpoints
- **`POST /api/v1/diagnoses`**: Trigger discrepancy classification for a validation ID.
- **`GET /api/v1/diagnoses/{diagnosis_id}`**: Retrieve structured discrepancy report.

---

## Verification & Reproducibility

Phase 5 has been verified with 88 dedicated unit tests in `tests/diagnosis/` covering:
- Signature hash determinism & deduplication.
- Priority rule evaluation & precedence (`NULL_SEMANTICS` over `AGGREGATION_SEMANTICS`).
- Order independence of input signals.
- Flagship boundary scenario CLI summary output formatting.
