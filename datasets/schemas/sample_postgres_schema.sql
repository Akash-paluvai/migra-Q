-- PostgreSQL Target DDL
CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    amount NUMERIC(12, 2),
    status VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
