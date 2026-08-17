import duckdb
con = duckdb.connect()
con.execute("CREATE TABLE sales_region AS SELECT i AS region_id, 'Region_' || (i % 10) AS region_name FROM range(1, 101) t(i)")
con.execute("CREATE TABLE monthly_sales AS SELECT i AS sale_id, (i % 10) + 1 AS region_id, (i * 25.0) AS revenue, (i % 12) + 1 AS sale_month, 2026 AS sale_year FROM range(1, 5001) t(i)")
try:
    sql = """
SELECT
    ms.region_id,
    COALESCE(sr.region_name, 'UNKNOWN') AS region_name,
    ms.sale_year,
    ms.sale_month,

    COUNT(*) AS sale_count,
    SUM(ms.revenue) AS total_revenue,
    AVG(ms.revenue) AS avg_revenue,

    SUM(SUM(ms.revenue)) OVER (
        PARTITION BY ms.region_id, ms.sale_year
    ) AS yearly_region_revenue,

    AVG(AVG(ms.revenue)) OVER (
        PARTITION BY ms.sale_year, ms.sale_month
    ) AS monthly_avg_revenue,

    LAG(SUM(ms.revenue)) OVER (
        PARTITION BY ms.region_id
        ORDER BY ms.sale_year, ms.sale_month
    ) AS previous_month_revenue,

    ROW_NUMBER() OVER (
        PARTITION BY ms.sale_year, ms.sale_month
        ORDER BY SUM(ms.revenue) DESC
    ) AS revenue_rank

FROM monthly_sales ms
LEFT JOIN sales_region sr
    ON ms.region_id = sr.region_id

WHERE ms.sale_year BETWEEN 2025 AND 2026
  AND ms.revenue IS NOT NULL

GROUP BY
    ms.region_id,
    sr.region_name,
    ms.sale_year,
    ms.sale_month

QUALIFY
    ROW_NUMBER() OVER (
        PARTITION BY ms.sale_year, ms.sale_month
        ORDER BY SUM(ms.revenue) DESC
    ) <= 3

ORDER BY
    ms.sale_year DESC,
    ms.sale_month DESC,
    revenue_rank;
"""
    con.execute(sql)
    print("DuckDB Executed Successfully!")
except Exception as e:
    print(f"DuckDB Error: {e}")
