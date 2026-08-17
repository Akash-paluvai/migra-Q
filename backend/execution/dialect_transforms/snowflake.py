import sqlglot.expressions as exp

def transform_snowflake_rules(node: exp.Expression) -> exp.Expression:
    """Transform Snowflake-specific AST nodes to DuckDB compatible nodes."""
    return node
