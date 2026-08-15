-- Multi-table JOIN Benchmark Query
SELECT 
    c.customer_id,
    a.account_id,
    t.transaction_id,
    t.amount
FROM customers c
INNER JOIN accounts a ON c.customer_id = a.customer_id
LEFT JOIN transactions t ON a.account_id = t.account_id
WHERE a.status = 'ACTIVE';
