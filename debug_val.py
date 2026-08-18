import duckdb
con = duckdb.connect()
dataset_dir = "datasets/generated/join_semantics"
con.execute(f"CREATE VIEW primary_entity AS SELECT * FROM read_parquet('{dataset_dir}/primary_entity.parquet')")
con.execute(f"CREATE VIEW secondary_entity AS SELECT * FROM read_parquet('{dataset_dir}/secondary_entity.parquet')")

s1 = "SELECT p.ref_code, COUNT(s.detail_id) AS detail_count FROM primary_entity p LEFT JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code"
s2 = "SELECT p.ref_code, COUNT(s.detail_id) AS detail_count FROM primary_entity p INNER JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code"

print("s1:", con.execute(s1).fetchall()[:2])
print("s2:", con.execute(s2).fetchall()[:2])
