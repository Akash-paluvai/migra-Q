from sqlglot import exp


class RuleExtractor:
    """Extracts implicit business rules, WHERE predicates, joins, and aggregates from ASTs."""

    @staticmethod
    def extract_predicates(expression: exp.Expression) -> list[str]:
        """Extract WHERE conditions as assertions."""
        predicates = []
        where_clause = expression.find(exp.Where)
        if where_clause:
            for condition in where_clause.this.flatten():
                predicates.append(condition.sql())
        return predicates

    @staticmethod
    def extract_aggregates(expression: exp.Expression) -> list[str]:
        """Extract aggregate functions (SUM, COUNT, AVG, MIN, MAX)."""
        aggregates = []
        for agg in expression.find_all(exp.AggFunc):
            aggregates.append(agg.sql())
        return aggregates

    @staticmethod
    def extract_groupings(expression: exp.Expression) -> list[str]:
        """Extract GROUP BY columns."""
        group_by = expression.find(exp.Group)
        if group_by:
            return [arg.sql() for arg in group_by.expressions]
        return []
