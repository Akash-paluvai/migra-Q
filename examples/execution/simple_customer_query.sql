SELECT
    customer_id,
    first_name,
    last_name,
    customer_segment,
    annual_income
FROM customers
WHERE customer_segment = 'PREMIUM'
ORDER BY annual_income DESC;
