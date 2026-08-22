# Terminology

This glossary defines the core concepts and vocabulary used throughout the Migra-Q platform.

### Schema Preflight
- **Definition**: A deterministic check performed on a SQL candidate before execution to ensure all referenced columns actually exist in the target dataset.
- **Why it exists**: To prevent generic database `Binder Error: column not found` exceptions from masking what is fundamentally an input configuration error.
- **Where it appears**: Between Translation and Execution (Phase 3.5 equivalent).
- **Example**: If `transactions.refund_amount` is queried but the schema only contains `transaction_id, amount`, Preflight catches it.

### Input Schema Mismatch
- **Definition**: The specific failure reason when Schema Preflight fails.
- **Why it exists**: To differentiate a bad query configuration from a semantic failure.
- **Where it appears**: In the UI as a `BLOCKED` state warning: "Execution was not attempted. Choose another dataset or edit the query to continue."
- **Example**: Attempting to run a customer risk query against a dataset that lacks risk scores.

### Semantic Discrepancy
- **Definition**: A mismatch in the output data between the source execution and the target execution despite both executing successfully.
- **Why it exists**: SQL dialects handle edge cases (e.g., NULL sorting, division by zero, rounding) differently.
- **Where it appears**: Discovered by the Validation Engine and analyzed by AI Diagnosis.
- **Example**: Source SQL sorts `NULLS FIRST` implicitly, while Target SQL sorts `NULLS LAST` implicitly.

### Behavioral Drift
- **Definition**: The long-term accumulation of Semantic Discrepancies across many migrations, leading to divergent analytics platforms.
- **Why it exists**: To articulate the enterprise risk that Migra-Q prevents.
- **Where it appears**: In high-level architecture documentation and Assurance reporting.
- **Example**: A dashboard showing 5% less revenue on Snowflake compared to Teradata because Snowflake handled date truncation differently.

### Hard Gate
- **Definition**: A strict condition in the pipeline that must be met to proceed. Failure immediately halts the migration.
- **Why it exists**: To enforce deterministic safety and prevent compounding errors.
- **Where it appears**: Execution, Schema Preflight, Lineage Validation.
- **Example**: If the `source_sql_hash` of an artifact doesn't match the migration record, the Lineage Hard Gate blocks it.

### Verification Path
- **Definition**: The route a migration takes through the Validation engine to achieve a `VERIFIED` state.
- **Why it exists**: To track whether a migration succeeded on the first try or required AI intervention.
- **Where it appears**: In the Assurance Scorecard.
- **Example**: A migration might take the `Direct Pass` path or the `Repaired Pass` path.

### Direct Pass
- **Definition**: A migration that passes all Validation stages on the first attempt without AI Repair.
- **Why it exists**: It represents the highest confidence score for a migration.
- **Where it appears**: Assurance reporting.

### Repaired Pass
- **Definition**: A migration that initially failed Validation, but was successfully patched by AI Repair and passed re-verification.
- **Why it exists**: To acknowledge that the final SQL is semantically identical, but required modification from the initial LLM translation.
- **Where it appears**: Assurance reporting.

### Repair Failed
- **Definition**: A migration where AI Diagnosis proposed a patch, but the repaired SQL still failed Validation.
- **Why it exists**: To prevent bad AI patches from slipping into production.
- **Where it appears**: Leads to a `BLOCKED` final state.

### Not Executed
- **Definition**: A status indicating a downstream phase was skipped because an upstream Hard Gate blocked it.
- **Why it exists**: To accurately distinguish between a test that *failed* and a test that *didn't run*.
- **Where it appears**: Validation and Verification steps when Execution or Preflight fails.

### Provider Limit
- **Definition**: When an external LLM API (like OpenAI or Gemini) exhausts its quota or rate limits.
- **Why it exists**: To cleanly handle third-party dependency outages.
- **Where it appears**: Final status `BLOCKED_PROVIDER_LIMIT`.

### Assurance Score
- **Definition**: A normalized, quantitative score (0-100) representing the confidence that the target SQL is semantically identical to the source.
- **Why it exists**: To give stakeholders a single metric to gate deployments.
- **Where it appears**: Phase 9 Assurance, displayed prominently on the UI Dashboard.
- **Example**: A Direct Pass with full data coverage yields 100/100.

### Evidence Coverage
- **Definition**: The percentage or depth of data rows tested against the validation engine.
- **Why it exists**: Testing on 10 rows provides less assurance than testing on 1,000,000 rows.
- **Where it appears**: An input factor to the Assurance Score.

### Translation Candidate
- **Definition**: The raw SQL output generated by the LLM during Phase 3, before it has been executed or verified.
- **Why it exists**: To establish that LLM output is merely a *candidate*, not the final truth.
- **Where it appears**: Translation Phase UI and API models.

### AST Normalization
- **Definition**: The process of converting SQL into a generic Abstract Syntax Tree (via `sqlglot`) to ignore stylistic differences (whitespace, casing).
- **Why it exists**: So the AI Diagnosis agent doesn't waste time analyzing formatting changes.
- **Where it appears**: Before Discrepancy Diffing.

### Dialect Translation
- **Definition**: Converting SQL syntax from a source engine (e.g., Oracle) to a target engine (e.g., Snowflake).
- **Why it exists**: The primary function of the platform.
- **Where it appears**: Phase 3.

### Deterministic Verification
- **Definition**: The concept of relying on exact mathematical or logical equivalence in execution outputs rather than LLM assertions.
- **Why it exists**: The core architectural philosophy of Migra-Q.
- **Where it appears**: Throughout the platform's design and in `APPROACH.md`.
