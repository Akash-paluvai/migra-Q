-- NULL Handling Benchmark Query
SELECT 
    customer_id,
    COALESCE(account_id, 'NO_ACCOUNT') AS account_ref,
    ZEROIFNULL(amount) AS safe_amount
FROM transactions;
