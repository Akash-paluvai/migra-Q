import sqlglot.expressions as exp

from .common import transform_common_sandbox_rules
from .oracle import transform_oracle_rules
from .teradata import transform_teradata_rules
from .bigquery import transform_bigquery_rules
from .snowflake import transform_snowflake_rules

def transform_for_duckdb(node: exp.Expression, dialect: str) -> exp.Expression:
    """Master routing function for AST transformations to DuckDB."""
    
    # 1. Apply dialect-specific rules first
    if dialect == "oracle":
        node = transform_oracle_rules(node)
    elif dialect == "teradata":
        node = transform_teradata_rules(node)
    elif dialect == "bigquery":
        node = transform_bigquery_rules(node)
    elif dialect == "snowflake":
        node = transform_snowflake_rules(node)
        
    # 2. Apply common sandbox rules (e.g. table prefix stripping)
    node = transform_common_sandbox_rules(node)
    
    return node
