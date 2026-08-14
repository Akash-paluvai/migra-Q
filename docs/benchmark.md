# Benchmark Suite Documentation

## Evaluation Metrics

- **Translation Accuracy Rate**: Percentage of test queries translated without AST error.
- **Validation Pass Rate**: Percentage of translated queries passing all 5 validation gates.
- **Repair Success Rate**: Percentage of failing queries repaired automatically by the repair agent.
- **Average Latency (ms)**: End-to-end execution time in DuckDB sandbox.

## Target Dialect Pairs
- Oracle PL/SQL ➔ PostgreSQL
- Snowflake ➔ Google BigQuery
- MySQL ➔ SQLite / DuckDB
