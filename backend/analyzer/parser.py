import sqlglot
from sqlglot import exp
from backend.core.exceptions import ParserException
from backend.core.logging import logger


class SQLParser:
    """Parses SQL queries into sqlglot AST representations for arbitrary dialects."""

    @staticmethod
    def parse_sql(sql: str, dialect: str) -> exp.Expression:
        """Parse raw SQL string into an AST Expression."""
        try:
            parsed = sqlglot.parse_one(sql, read=dialect.lower())
            if parsed is None:
                raise ParserException(f"Failed to parse SQL query for dialect '{dialect}'")
            return parsed
        except Exception as e:
            logger.error(f"SQL parsing failed for dialect {dialect}: {str(e)}")
            raise ParserException(f"SQL Parsing error in {dialect}: {str(e)}")

    @staticmethod
    def get_tables(expression: exp.Expression) -> list[str]:
        """Extract table names referenced in the query."""
        tables = set()
        for table in expression.find_all(exp.Table):
            tables.add(table.name)
        return sorted(list(tables))

    @staticmethod
    def get_columns(expression: exp.Expression) -> list[str]:
        """Extract column names referenced in the query."""
        columns = set()
        for col in expression.find_all(exp.Column):
            columns.add(col.name)
        return sorted(list(columns))
