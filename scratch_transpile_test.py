import sqlglot

sql = """
SELECT `monthly_sales`.`region_id` AS `region_id`
FROM `monthly_sales`
"""

transpiled = sqlglot.transpile(sql, read="bigquery", write="duckdb")[0]
print(transpiled)
