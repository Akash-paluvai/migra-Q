import duckdb

dataset_dir = "datasets/generated/customer_risk"
con = duckdb.connect()
con.execute(f"CREATE VIEW customers AS SELECT * FROM read_parquet('{dataset_dir}/customers.parquet')")
con.execute(f"CREATE VIEW transactions AS SELECT * FROM read_parquet('{dataset_dir}/transactions.parquet')")

sql = """SELECT c.customer_segment, c.risk_tier, COUNT(DISTINCT c.customer_id) AS customer_count, COUNT(DISTINCT CASE WHEN t.status = 'COMPLETED' THEN t.transaction_id END) AS completed_transaction_count, SUM(CASE WHEN t.status = 'COMPLETED' THEN t.amount ELSE 0 END) AS completed_amount, SUM(CASE WHEN t.status <> 'COMPLETED' OR t.status IS NULL THEN t.amount ELSE 0 END) AS non_completed_amount, AVG(CASE WHEN t.status = 'COMPLETED' THEN t.amount END) AS avg_completed_amount, MAX(t.amount) AS max_transaction_amount, COUNT(DISTINCT CASE WHEN t.amount >= 5000 THEN c.customer_id END) AS high_value_customers, CASE WHEN COUNT(DISTINCT c.customer_id) >= 100 AND SUM(CASE WHEN t.status = 'COMPLETED' THEN t.amount ELSE 0 END) >= 500000 THEN 'CRITICAL_SEGMENT' WHEN COUNT(DISTINCT c.customer_id) >= 50 OR SUM(CASE WHEN t.status = 'COMPLETED' THEN t.amount ELSE 0 END) >= 250000 THEN 'HIGH_SEGMENT' ELSE 'NORMAL_SEGMENT' END AS segment_risk FROM customers AS c LEFT JOIN transactions AS t ON c.customer_id = t.customer_id WHERE c.status = 'ACTIVE' GROUP BY c.customer_segment, c.risk_tier QUALIFY RANK() OVER (PARTITION BY c.customer_segment ORDER BY SUM(CASE WHEN t.status = 'COMPLETED' THEN t.amount ELSE 0 END) DESC, COUNT(DISTINCT c.customer_id) DESC) <= 3 ORDER BY c.customer_segment NULLS FIRST, segment_risk NULLS FIRST, completed_amount DESC"""

try:
    con.execute(sql).fetchall()
except Exception as e:
    print("Execution failed!")
    print(e)
