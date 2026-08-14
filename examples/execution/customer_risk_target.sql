SELECT
    c.customer_id,
    c.customer_segment,
    SUM(t.amount) AS total_amount,
    CASE
        WHEN t.amount >= 500 THEN 'HIGH_RISK'
        ELSE 'NORMAL'
    END AS risk_class
FROM transactions AS t
INNER JOIN customers AS c
    ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;
