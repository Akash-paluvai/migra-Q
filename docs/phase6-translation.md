# Phase 6 — AI-Assisted SQL Translation Engine

## 1. Overview & Core Philosophy

Phase 6 introduces generative AI translation capabilities into MIGRA-Q.

```text
               Translation Request
                        │
                        ▼
            ┌──────────────────────┐
            │ Phase 1 SQL Analyzer │  (source_dialect)
            └──────────┬───────────┘
                       │
                       ▼
                  SQLAnalysis
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
    Schema         SQL Rules       Dialects
       │               │               │
       └───────────────┼───────────────┘
                       ▼
             Translation Context  (translation_context_hash)
                       │
                       ▼
               Prompt Builder    (prompt_hash)
                       │
                       ▼
               LLM Provider
             ┌─────────┴─────────┐
             │                   │
        OpenAIProvider      MockProvider (4 Scenarios)
             │                   │
             └─────────┬─────────┘
                       ▼
             Structured Response (Pydantic Check)
                       │
                       ▼
            Candidate SQL Validator
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          Parse    Read-only   Schema Consistency
             │         │         │
             └─────────┼─────────┘
                       ▼
              TranslationResult  (Candidate SQL syntactically valid)
                       │
                       ▼
                 PostgreSQL  (STOP! No auto Phase 3/4/5 invocation)
```

> [!IMPORTANT]
> **Core Architecture Guarantee**: AI generates candidate SQL ($ \text{Source SQL} \to \text{Target SQL Candidate} $). The deterministic pipeline (Phase 3 execution, Phase 4 validation, Phase 5 classification) remains the sole authority for judging equivalence and correctness. The LLM never claims or decides equivalence, production readiness, or approval.

---

## 2. Provider Abstraction

The system interacts with generative models via the `LLMProvider` abstract interface defined in [`provider.py`](file:///Users/akashpaluvai/college/migraq/backend/translator/provider.py):

- **`OpenAIProvider`**: Uses the official `openai` Python SDK to generate structured JSON migrations.
- **`MockLLMProvider`**: Provides zero-network, 100% deterministic test scenarios:
  1. `MOCK_GOOD`: Valid, structurally faithful BigQuery SQL.
  2. `MOCK_BOUNDARY_BUG`: Intentionally changes `> 500` to `>= 500` to verify phase boundary separation.
  3. `MOCK_HALLUCINATED_COLUMN`: Uses nonexistent columns to test schema consistency enforcement.
  4. `MOCK_UNSAFE_SQL`: Generates mutating `DROP TABLE` SQL to test read-only safety policy.

---

## 3. Configuration & Auditability Hashes

Configuration settings in [`config.py`](file:///Users/akashpaluvai/college/migraq/backend/core/config.py):
- `LLM_PROVIDER`: `"mock"` (default) or `"openai"`.
- `LLM_MODEL`: Configurable string (e.g. `"gpt-4o"`).
- `LLM_API_KEY`: Read from environment (never committed or logged!).

Auditability Hashes:
- **`source_sql_hash`**: Normalized SHA-256 hash of source SQL.
- **`translation_context_hash`**: SHA-256 hash over source SQL, source/target dialects, schema context, AST analysis, and `PROMPT_VERSION`.
- **`prompt_hash`**: SHA-256 hash over system prompt, user prompt, and version.

---

## 4. Candidate Target SQL Validation

The candidate SQL validator ([`validator.py`](file:///Users/akashpaluvai/college/migraq/backend/translator/validator.py)) performs three safety and integrity checks:
1. **Read-Only Safety Check**: Rejects mutating statements (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, etc.) with status `UNSAFE_SQL`.
2. **Target Syntax Parsing**: Parses candidate SQL using SQLGlot for the target dialect (`VALID_SYNTAX` vs `INVALID_SYNTAX`).
3. **Schema Consistency Check**: Validates referenced tables and columns against `SchemaContext` (`SCHEMA_MISMATCH`).

Reports explicitly state `"Candidate SQL syntactically valid"`, NEVER `"Migration valid"`.

---

## 5. Usage Examples

### CLI Execution
```bash
python -m backend.translator.cli translate \
  --input examples/translation/customer_risk.sql \
  --source-dialect teradata \
  --target-dialect bigquery \
  --provider mock \
  --mock-mode MOCK_GOOD
```

### REST API
```http
POST /api/v1/translations
Content-Type: application/json

{
  "source_sql": "SELECT customer_id FROM transactions WHERE amount > 500;",
  "source_dialect": "teradata",
  "target_dialect": "bigquery"
}
```

---

## 6. Phase Boundary Isolation & Evaluation

Phase 6 ends strictly at `TranslationResult`. It does NOT invoke Phase 3 execution, Phase 4 semantic validation, or Phase 5 discrepancy classification.

Phase 6 evaluation measures **Candidate Generation Quality** (parse success, dialect syntax success, table/column retention, business rule representation). It does NOT measure semantic equivalence.
