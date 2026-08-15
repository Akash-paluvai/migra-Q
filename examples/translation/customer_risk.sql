-- Customer Risk Benchmark Query (Teradata source)
SELECT 
    c.customer_id,
    c.customer_segment,
    SUM(t.amount) AS total_amount,
    CASE 
        WHEN SUM(t.amount) > 500.00 THEN 'HIGH_RISK'
        ELSE 'NORMAL'
    END AS risk_class
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment;
