import sqlglot.expressions as exp

def transform_bigquery_rules(node: exp.Expression) -> exp.Expression:
    """Transform BigQuery-specific AST nodes to DuckDB compatible nodes."""
    
    # Transform BigQuery's ARRAY_AGG(val ORDER BY order_col [ASC|DESC] LIMIT 1)[OFFSET(0)]
    if isinstance(node, exp.Bracket):
        inner = node.this
        if isinstance(inner, exp.Paren):
            inner = inner.this
            
        if isinstance(inner, (exp.GroupConcat, exp.ArrayAgg)):
            limit_node = inner.this
            if isinstance(limit_node, exp.Limit):
                order_node = limit_node.this
                if isinstance(order_node, exp.Order):
                    val_col = order_node.this
                    order_exp = order_node.expressions[0]
                    order_col = order_exp.this
                    is_desc = order_exp.args.get("desc")
                    
                    limit_val = limit_node.expression.name if hasattr(limit_node.expression, "name") else str(limit_node.expression)
                    if limit_val == "1":
                        if is_desc:
                            return exp.Anonymous(this="arg_max", expressions=[val_col, order_col])
                        else:
                            return exp.Anonymous(this="arg_min", expressions=[val_col, order_col])
    
    return node
