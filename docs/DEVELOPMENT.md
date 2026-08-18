# Development & Debugging Guide

This guide covers how to set up the Migra-Q development environment, run tests, and effectively debug migration failures.

## Local Environment Setup

### 1. Python Backend
Migra-Q requires Python 3.11+.

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies in editable mode
pip install -e .

# Copy environment variables
cp .env.example .env
```

Ensure your `.env` contains valid API keys for the LLM providers (e.g., `GEMINI_API_KEY`, `OPENAI_API_KEY`) if you intend to run full end-to-end migrations.

**Run the backend server:**
```bash
uvicorn backend.main:app --reload --port 8000
```

### 2. React Frontend
The frontend uses React, TypeScript, and Vite.

```bash
cd frontend
npm install

# Run the development server
npm run dev
```

## Running Tests

The backend test suite uses `pytest`.

```bash
# Run all tests
pytest tests/

# Run specific modules
pytest tests/orchestrator/
pytest tests/validation/
```

We strictly enforce isolation. Ensure that your tests do not mutate `migraq.db` outside of test transactions.

## The Failure & Debugging Workflow

Because Migra-Q is a multi-phase orchestration pipeline, a failure can occur at several Hard Gates. When a migration fails, do not jump straight to the translation code.

Instead, **inspect in this order:**

1. **Migration Overview**: What is the final status? (`FAILED`, `BLOCKED`, `BLOCKED_PROVIDER_LIMIT`)
2. **Schema Preflight**: Did the query fail immediately because it referenced missing columns? If so, this is an `INPUT_SCHEMA_MISMATCH`. Fix the dataset configuration, not the translation prompt.
3. **Translation Artifact**: Did the LLM return valid SQL, or did it hallucinate markdown/explanation blocks that broke the parser?
4. **Execution Evidence**: Did DuckDB throw a `Binder Error` or `Syntax Error`? Check the `error_message` in the execution artifact.
5. **Validation Discrepancies**: If execution succeeded, did the Validation engine catch a mismatch? Check the Row Validator or Aggregate Validator diffs.
6. **AI Diagnosis**: What did the agent identify as the root cause? (e.g., `NULLS FIRST` vs `NULLS LAST`).
7. **Repair Proposal**: Did the AST patch attempt to fix the exact diagnosis?
8. **Verification Evidence**: Did the repaired SQL pass re-execution?
9. **Assurance Gates**: Did the migration fail a final Hard Gate (e.g., Lineage Mismatch)?
10. **Provider Logs**: Are you hitting rate limits? (Status: `BLOCKED_PROVIDER_LIMIT`).

By following this deterministic order, you align your debugging process with the pipeline's execution flow.
