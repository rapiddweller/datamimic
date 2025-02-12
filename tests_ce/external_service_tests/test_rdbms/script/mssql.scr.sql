USE master;


-- Check if 'simple' schema exists
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'simple')
BEGIN
    EXEC('CREATE SCHEMA simple');
END

-- Drop tables if they exist
DROP TABLE IF EXISTS simple.[user];
DROP TABLE IF EXISTS simple.customer;

-- Check if 'customer' table exists in the 'simple' schema
IF OBJECT_ID(N'simple.customer', N'U') IS NULL
BEGIN
    -- Create the "customer" table in the 'simple' schema
    CREATE TABLE simple.customer (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tc_creation_src NVARCHAR(255),
        tc_creation DATETIME2 NOT NULL,
        tc_update_src NVARCHAR(255),
        tc_update DATETIME2,
        no NVARCHAR(20) NOT NULL,
        name NVARCHAR(100),
        active BIT NOT NULL,
        CONSTRAINT UQ_customer_id UNIQUE (id)
    );
END


-- Check if 'user' table exists in the 'simple' schema
IF OBJECT_ID(N'simple.[user]', N'U') IS NULL
BEGIN
    -- Create the "user" table in the 'simple' schema
    CREATE TABLE simple.[user] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tc_creation_src NVARCHAR(255),
        tc_creation DATETIME2 NOT NULL,
        tc_update_src NVARCHAR(255),
        tc_update DATETIME2,
        full_name NVARCHAR(100),
        email NVARCHAR(255) NOT NULL,
        hashed_password NVARCHAR(255) NOT NULL,
        active BIT,
        superuser BIT,
        language NVARCHAR(50),
        customer_id INT,
        FOREIGN KEY (customer_id) REFERENCES simple.customer (id)
    );
END

