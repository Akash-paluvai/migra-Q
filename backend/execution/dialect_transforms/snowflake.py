import sqlglot.expressions as exp

def transform_snowflake_rules(node: exp.Expression) -> exp.Expression:
    """Transform Snowflake-specific AST nodes to DuckDB compatible nodes."""
    if isinstance(node, exp.ToChar):
        format_val = node.args.get("format")
        if format_val and isinstance(format_val, exp.Literal) and format_val.is_string:
            fmt_str = format_val.this
            new_fmt = fmt_str.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
            new_fmt = new_fmt.replace("yyyy", "%Y").replace("mm", "%m").replace("dd", "%d")
            return exp.TimeToStr(
                this=node.this,
                format=exp.Literal.string(new_fmt)
            )
    return node
