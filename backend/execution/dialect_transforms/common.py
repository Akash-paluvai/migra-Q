import sqlglot.expressions as exp

def transform_common_sandbox_rules(node: exp.Expression) -> exp.Expression:
    """Apply common Sandbox transformations regardless of dialect."""
    # Strip catalog and db from tables so they execute against DuckDB local temp tables/views
    if isinstance(node, exp.Table):
        node.set("db", None)
        node.set("catalog", None)
    return node
