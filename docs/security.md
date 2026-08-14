# Security & Privacy Guidelines

- **Sandboxed Execution**: Validation queries run strictly within isolated in-memory DuckDB processes with resource limits (`DUCKDB_MEMORY_LIMIT`).
- **Data Privacy**: No production row data is transferred to external LLM endpoints. Only AST structures and schema metadata are sanitized and passed to translation models if LLM fallback is triggered.
- **Credential Handling**: Database connection strings and API keys are loaded via environment variables (`.env`) and never stored in persistent code repositories.
