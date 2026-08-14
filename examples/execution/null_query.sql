SELECT
    account_id,
    customer_id,
    COALESCE(closed_at, '9999-12-31') AS effective_closed_at
FROM accounts
WHERE closed_at IS NULL;
