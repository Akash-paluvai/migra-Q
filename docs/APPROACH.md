# The Migra-Q Approach

Migra-Q operates on a core philosophical principle: **An LLM-generated explanation never overrides execution evidence.**

## AI Proposes, Determinism Decides

In traditional AI-assisted migrations, large language models (LLMs) are often trusted implicitly. A user prompts the LLM to translate Teradata to BigQuery, and the result is assumed correct unless it explicitly fails in production. 

Migra-Q rejects this approach.

Instead, Migra-Q enforces a strict hierarchy of authority where deterministic execution is always the final arbiter of truth.

### The Lifecycle of Authority

```text
LLM Translation
      ↓
Candidate SQL
      ↓
Deterministic Schema Preflight
      ↓
Deterministic Execution
      ↓
Deterministic Validation
      ↓
AI Diagnosis (when needed)
      ↓
AI Repair Proposal
      ↓
Deterministic Re-execution
      ↓
Deterministic Verification
      ↓
Assurance Decision
```

1. **The LLM is a heuristic proposer.** It generates the initial `Candidate SQL` and, if discrepancies are found later, it generates an `AI Repair Proposal`.
2. **The Execution Sandbox is the objective reality.** The candidate SQL is executed within a DuckDB sandbox. If the syntax is invalid for the dialect, the migration fails.
3. **The Validation Engine is the ultimate judge.** The outputs of the source execution and the target execution are compared deterministically. If the row sets differ, or NULLs are handled differently, the validation fails. 

## The Fallacy of AI "Self-Correction"

If a migration exhibits a discrepancy (e.g., `NULLS FIRST` vs `NULLS LAST`), an LLM might confidently assert that its translation is semantically identical. 

In Migra-Q, the LLM is not allowed to mark its own homework. 

The AI Diagnosis agent is invoked only to classify the discrepancy and propose a patch. The proposed patch is never blindly accepted. It must be re-injected into the pipeline, re-executed against the sandbox, and re-verified against the original source data by the Validation Engine. Only when the deterministic validators return a `VERIFIED` state does the migration proceed.
