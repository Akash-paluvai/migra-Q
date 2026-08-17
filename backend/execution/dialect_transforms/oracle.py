import sqlglot.expressions as exp

def transform_oracle_rules(node: exp.Expression) -> exp.Expression:
    """Transform Oracle-specific AST nodes to DuckDB compatible nodes."""
    
    # Oracle KEEP (DENSE_RANK ...)
    if isinstance(node, exp.Window) and isinstance(node.args.get("over"), str) and node.args.get("over").upper() == "KEEP":
        val_col = node.this.this if isinstance(node.this, (exp.Max, exp.Min)) else None
        
        order_node = node.args.get("order")
        if val_col and order_node and order_node.expressions:
            order_exp = order_node.expressions[0]
            order_col = order_exp.this
            
            # Extract direction flags
            is_desc = order_exp.args.get("desc") or False
            is_first = node.args.get("first") or False  # True=FIRST, False=LAST
            
            # Map combinations to arg_max / arg_min
            if is_first:
                # FIRST: return the value from the top of the ordered list
                # ASC  -> top is min value of order_col -> arg_min
                # DESC -> top is max value of order_col -> arg_max
                use_arg_max = is_desc
            else:
                # LAST: return the value from the bottom of the ordered list
                # ASC  -> bottom is max value of order_col -> arg_max
                # DESC -> bottom is min value of order_col -> arg_min
                use_arg_max = not is_desc
                
            func_name = "arg_max" if use_arg_max else "arg_min"
            return exp.Anonymous(this=func_name, expressions=[val_col, order_col])
            
    return node
