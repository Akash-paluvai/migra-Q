import sqlglot.expressions as exp

def transform_netezza_rules(node: exp.Expression) -> exp.Expression:
    """Transform Netezza-specific AST nodes to DuckDB compatible nodes."""
    return node
