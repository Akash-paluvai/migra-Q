BENCHMARK_CASES = [
    {
        "case_id": "ORACLE_PG_01",
        "name": "Oracle NVL and SYSDATE to PostgreSQL",
        "source_dialect": "oracle",
        "target_dialect": "postgres",
        "source_sql": "SELECT id, NVL(amount, 0) AS total_amount, SYSDATE AS sync_date FROM transactions WHERE amount > 50",
        "sample_data": {
            "transactions": [
                {"id": 1, "amount": 100.0},
                {"id": 2, "amount": None},
                {"id": 3, "amount": 75.5}
            ]
        }
    },
    {
        "case_id": "SNOWFLAKE_BQ_01",
        "name": "Snowflake IFF and ZEROIFNULL to BigQuery",
        "source_dialect": "snowflake",
        "target_dialect": "bigquery",
        "source_sql": "SELECT customer_id, ZEROIFNULL(balance) AS clean_balance FROM accounts",
        "sample_data": {
            "accounts": [
                {"customer_id": 101, "balance": 500.0},
                {"customer_id": 102, "balance": None}
            ]
        }
    }
]
