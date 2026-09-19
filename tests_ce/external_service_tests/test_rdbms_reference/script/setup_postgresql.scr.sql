CREATE SCHEMA IF NOT EXISTS functional;

DROP TABLE IF EXISTS functional.ref_customers;
DROP TABLE IF EXISTS functional.ref_customers_composite;

CREATE TABLE functional.ref_customers (
    customer_id INT PRIMARY KEY,
    tier VARCHAR(20)
);

CREATE TABLE functional.ref_customers_composite (
    cust_id INT PRIMARY KEY,
    region VARCHAR(20)
);
