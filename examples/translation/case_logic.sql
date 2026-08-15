-- CASE Logic Benchmark Query
SELECT 
    transaction_id,
    amount,
    CASE 
        WHEN amount >= 1000 THEN 'PLATINUM'
        WHEN amount >= 500 THEN 'GOLD'
        WHEN amount > 0 THEN 'SILVER'
        ELSE 'ZERO'
    END AS tier
FROM transactions;
