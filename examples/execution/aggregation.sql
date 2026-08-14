SELECT
    account_type,
    COUNT(*) AS total_accounts,
    SUM(balance) AS total_balance,
    AVG(balance) AS avg_balance
FROM accounts
GROUP BY account_type;
