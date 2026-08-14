-- Oracle Source DDL
CREATE TABLE transactions (
    transaction_id NUMBER(10) PRIMARY KEY,
    customer_id NUMBER(10) NOT NULL,
    amount NUMBER(12, 2),
    status VARCHAR2(20),
    created_at TIMESTAMP DEFAULT SYSDATE
);
