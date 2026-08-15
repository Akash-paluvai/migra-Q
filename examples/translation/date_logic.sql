-- Date Logic Benchmark Query
SELECT 
    customer_id,
    transaction_id,
    created_at,
    EXTRACT(YEAR FROM created_at) AS tx_year
FROM transactions;
