# The Migra-Q Approach

Migra-Q operates on a core philosophical principle: **An LLM-generated explanation never overrides execution evidence, and sandbox execution never overrides true semantic equivalence.**

## AI Proposes, Determinism Decides

In traditional AI-assisted migrations, large language models (LLMs) are often trusted implicitly. A user prompts the LLM to translate Teradata to BigQuery, and the result is assumed correct unless it explicitly fails in production. 

Migra-Q rejects this approach.

Instead, Migra-Q enforces a strict hierarchy of authority where deterministic execution is always the final arbiter of truth. However, execution alone is not enough.

### The Lifecycle of Authority

```text
LLM Translation (Source/Target Dialects)
      ↓
Candidate SQL
      ↓
Deterministic Schema Preflight
      ↓
Capability Sandbox Analysis (Compatibility Adapters)
      ↓
Deterministic Execution (DuckDB Sandbox)
      ↓
Deterministic Validation
      ↓
Semantic Assurance Gating
```

1. **The LLM is a heuristic proposer.** It generates the initial `Candidate SQL`.
2. **Dialect Compatibility Adapters bridge proven gaps.** They translate known dialect-specific syntax (e.g., Teradata's `ZEROIFNULL`) into DuckDB-compatible syntax, attaching a `SemanticConfidence` to the transformation. We do *not* use a massive, speculative function registry; we only use adapters for proven semantic compatibility gaps.
3. **The Execution Sandbox is an isolated validator, NOT the authority.** DuckDB executes the patched SQL to prove syntax and runtime safety. If DuckDB fails to execute the query due to an unsupported proprietary signature, we correctly classify it as a `SANDBOX_UNSUPPORTED_FUNCTION_SIGNATURE` rather than pretending it was an `EXECUTION_ERROR`.
4. **The Validation Engine is the ultimate judge of rows.** The outputs of the source execution and the target execution are compared deterministically.
5. **The Assurance Gate prevents false confidence.** Even if DuckDB validation passes, if the Dialect Adapter applied an `APPROXIMATION` or `UNKNOWN` transformation, the final state is coerced to `INCONCLUSIVE`. The sandbox cannot independently promote approximations to `VERIFIED`.

## The Fallacy of AI "Self-Correction"

If a migration exhibits a discrepancy (e.g., `NULLS FIRST` vs `NULLS LAST`), an LLM might confidently assert that its translation is semantically identical. 

In Migra-Q, the LLM is not allowed to mark its own homework. 

The AI Diagnosis agent is invoked only to classify the discrepancy and propose a patch. The proposed patch is never blindly accepted. It must be re-injected into the pipeline, re-analyzed by the capability adapters, re-executed against the sandbox, and re-verified against the original source data by the Validation Engine. Only when the deterministic validators return a `VERIFIED` state (and confidence is at least `SAFE_EQUIVALENT`) does the migration proceed.
