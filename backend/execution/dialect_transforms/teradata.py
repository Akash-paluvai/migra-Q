import sqlglot.expressions as exp

def transform_teradata_rules(node: exp.Expression) -> exp.Expression:
    """Transform Teradata-specific AST nodes to DuckDB compatible nodes.
    
    Standard sqlglot handles TOP, QUALIFY, and standard window functions seamlessly.
    Reserved for handling quirky date math or proprietary string casting logic later.
    """
    return node
