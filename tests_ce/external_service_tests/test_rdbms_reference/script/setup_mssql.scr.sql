USE master

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'functional')
BEGIN
    EXEC('CREATE SCHEMA functional');
END;

DROP TABLE IF EXISTS functional.ref_customers;
DROP TABLE IF EXISTS functional.ref_customers_composite;

CREATE TABLE functional.ref_customers (
    customer_id INT PRIMARY KEY,
    tier NVARCHAR(20)
);

CREATE TABLE functional.ref_customers_composite (
    cust_id INT PRIMARY KEY,
    region NVARCHAR(20)
);
