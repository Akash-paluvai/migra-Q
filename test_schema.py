from backend.datasets.registry import DatasetRegistry
import duckdb

registry = DatasetRegistry()
print("Initialized Registry. Re-generating customer_risk if missing.")

con = duckdb.connect()
print("Customers Schema:")
print(con.execute("DESCRIBE SELECT * FROM read_parquet('datasets/generated/customer_risk/customers.parquet')").fetchall())

print("Transactions Schema:")
print(con.execute("DESCRIBE SELECT * FROM read_parquet('datasets/generated/customer_risk/transactions.parquet')").fetchall())
