-- Aggregation Benchmark Query
SELECT 
    customer_id,
    COUNT(transaction_id) AS total_tx_count,
    COUNT(*) AS row_count,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_spent,
    MAX(amount) AS max_spent
FROM transactions
GROUP BY customer_id;
