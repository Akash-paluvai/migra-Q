class RootCauseAnalyzer:
    """Analyzes AST structures and query diffs to isolate root cause patterns."""

    KNOWN_PATTERNS = {
        "NVL": "Oracle NVL vs PostgreSQL COALESCE handling of NULL values",
        "SYSDATE": "Oracle SYSDATE returns server time, Postgres CURRENT_TIMESTAMP includes timezone",
        "DECODE": "Oracle DECODE pattern requires translation to ANSI standard CASE WHEN",
        "ROWNUM": "Oracle ROWNUM vs Postgres LIMIT/OFFSET semantics",
    }

    @classmethod
    def analyze_source_sql(cls, source_sql: str) -> list[str]:
        findings = []
        for kw, explanation in cls.KNOWN_PATTERNS.items():
            if kw in source_sql.upper():
                findings.append(f"Potential dialect divergence detected: {explanation}")
        return findings
