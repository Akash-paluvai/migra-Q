# The Validation Engine

Migra-Q's Validation Engine is one of its primary technical differentiators. Because LLM translations can silently drift in semantic meaning, the Validation Engine performs a deterministic comparison between the source SQL execution and the target SQL execution.

This semantic validation is entirely independent of the AI Diagnosis phase. The AI only diagnoses *why* a discrepancy occurred; the Validation Engine determines *that* it occurred using strict mathematics and logic.

## The 5-Stage Framework

The Validation Engine evaluates execution outputs across five discrete layers:

### 1. Schema Validator
Ensures the structural contract of the query remains identical.
- Validates column counts.
- Validates column names (ignoring dialect-specific casing conventions).
- Validates basic type compatibility (e.g., ensuring `DECIMAL(10,2)` isn't truncated to `INTEGER`).

### 2. Row Validator
The most stringent check, performing a deep equality comparison of the returned row sets.
- Order is respected if an `ORDER BY` clause exists.
- Row counts must match exactly.
- **Normalization:** `NULL` and `NaN` values are normalized before equality comparison to prevent false positives from floating-point idiosyncrasies.

### 3. Aggregate Validator
Verifies mathematical correctness for queries utilizing `GROUP BY`, `SUM`, `AVG`, etc.
- Ensures floating-point aggregations fall within an acceptable epsilon.
- Validates that grouping sets align perfectly between dialects.

### 4. Business Rule Validator
Tests specific semantic behaviors that are prone to mistranslation across dialects.
- **Date Truncation:** e.g., how `DATE_TRUNC('month', timestamp)` behaves.
- **Division by Zero:** Ensures the target SQL handles errors or returns `NULL` exactly as the source did.
- **String Padding & Trimming:** Ensures whitespace semantics remain consistent.

### 5. Edge Case Validator
Executes the generated SQL against boundary conditions injected into the DuckDB sandbox.
- Tests extremely large numerics.
- Tests highly nested subqueries.
- Tests empty dataset behavior.

## Normalization & Strict Equality

A critical function of the Validation Engine is its pre-comparison normalization. For example, if Oracle returns a missing value as a specific internal representation, and Snowflake returns `NULL`, the engine normalizes these to a unified representation *before* asserting equality.

If the Row Validator finds that Row 5, Column 'Risk_Score' is `NULL` in the source but `0` in the target, it throws a `Semantic Discrepancy`. This discrepancy is then passed as evidence to the AI Diagnosis agent.
