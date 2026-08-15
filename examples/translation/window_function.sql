-- Window Function Benchmark Query
SELECT 
    customer_id,
    transaction_id,
    amount,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rank_num
FROM transactions;
