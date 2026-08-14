from backend.analyzer.parser import SQLParser


def test_sql_parser_extracts_tables():
    sql = "SELECT a.id, b.name FROM users a JOIN orders b ON a.id = b.user_id WHERE a.age > 18"
    expr = SQLParser.parse_sql(sql, "postgres")
    tables = SQLParser.get_tables(expr)
    assert "users" in tables
    assert "orders" in tables
