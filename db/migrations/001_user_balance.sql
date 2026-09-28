-- Apply once to the existing, authorized training MySQL 8.4 database.
-- Pause application writes before applying; MySQL DDL implicitly commits.
-- Do not rerun schema.sql or seed.sql against an existing database.
ALTER TABLE users
    ADD COLUMN balance NUMERIC(12, 2) NOT NULL DEFAULT 1000000.00,
    ADD CONSTRAINT ck_user_balance CHECK (balance >= 0);

START TRANSACTION;
UPDATE users SET balance = CASE username
    WHEN 'user1' THEN 500000.00
    WHEN 'user2' THEN 300000.00
    WHEN 'guest' THEN 100000.00
    WHEN 'test' THEN 200000.00
    WHEN 'shop' THEN 1000000.00
    WHEN 'admin' THEN 5000000.00
    ELSE balance END
WHERE username IN ('user1', 'user2', 'guest', 'test', 'shop', 'admin');
COMMIT;
