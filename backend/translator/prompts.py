PROMPT_SQL_TRANSLATION = """
You are an expert database migration engineer.
Translate the following {source_dialect} SQL query into accurate {target_dialect} SQL.

Source Query ({source_dialect}):
```sql
{source_sql}
```

Ensure:
1. Exact semantic preservation of functions, windowing, null logic, and date arithmetic.
2. Dialect-idiomatic type casting and functions.
3. Return ONLY valid SQL without markdown codeblock markers if requested, or inside standard ```sql ```.
"""

PROMPT_REPAIR_SQL = """
You are an expert database repair engineer.
The target {target_dialect} SQL query failed equivalence validation or execution.

Original Source ({source_dialect}):
```sql
{source_sql}
```

Current Target ({target_dialect}):
```sql
{target_sql}
```

Mismatch Analysis:
{mismatch_report}

Generate a repaired {target_dialect} query that resolves the mismatch completely.
"""
