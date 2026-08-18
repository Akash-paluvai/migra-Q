import shutil

def get_builtin_specs():
    return [
        ("customer_risk", "Customer Risk Benchmark", "CASE statements and threshold boundary condition benchmarks", ["boundary", "case", "benchmark"], "1.1"),
        ("customer_aggregation", "Aggregation & Metrics Lab", "GROUP BY, SUM, COUNT, and AVG aggregation benchmarks", ["aggregation", "group_by"], "1.0"),
        ("null_semantics", "Null Semantics & Coalesce Lab", "NULL comparison, COALESCE, and IS NULL filtering benchmarks", ["nulls", "coalesce"], "1.0"),
        ("join_semantics", "Join & Cardinality Lab", "INNER vs LEFT JOIN and duplicate key cardinality benchmarks", ["join", "cardinality"], "1.1"),
        ("date_semantics", "Date & Timestamp Lab", "Date boundaries, truncations, and timestamp extraction benchmarks", ["date", "timestamp"], "1.0"),
        ("mixed_business_logic", "Enterprise Multi-Rule Analytics", "Complex multi-rule enterprise analytics with mixed logic", ["enterprise", "mixed"], "1.0"),
        ("enterprise_metrics", "Enterprise Metrics Benchmark", "Enterprise KPI and metrics benchmark with 5000 rows", ["enterprise", "metrics"], "1.0"),
    ]
