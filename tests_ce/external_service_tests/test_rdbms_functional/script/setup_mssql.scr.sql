USE master

-- Check if 'functional' schema exists
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'functional')
BEGIN
    EXEC('CREATE SCHEMA functional');
END;

-- Drop tables if they exist
DROP TABLE IF EXISTS functional.[user];
DROP TABLE IF EXISTS functional.customer;
DROP TABLE IF EXISTS functional.simple_user;

-- Create table "customer"
IF OBJECT_ID(N'functional.customer', N'U') IS NULL
BEGIN
    CREATE TABLE functional.customer (
        id INTEGER PRIMARY KEY,
        tc_creation_src NVARCHAR(MAX),
        tc_creation DATETIME NOT NULL,
        tc_update_src NVARCHAR(MAX),
        tc_update DATETIME,
        no NVARCHAR(MAX) NOT NULL,
        name NVARCHAR(MAX),
        active BIT NOT NULL
    );
END;

-- Create table "[user]"
IF OBJECT_ID(N'functional.[user]', N'U') IS NULL
BEGIN
    DROP TABLE IF EXISTS functional.[user];
    CREATE TABLE functional.[user] (
        id INT PRIMARY KEY,
        tc_creation_src NVARCHAR(MAX),
        tc_creation DATETIME NOT NULL,
        tc_update_src NVARCHAR(MAX),
        tc_update DATETIME,
        full_name NVARCHAR(MAX),
        email NVARCHAR(MAX) NOT NULL,
        hashed_password NVARCHAR(MAX) NOT NULL,
        active BIT,
        superuser BIT,
        language NVARCHAR(MAX),
        customer_id INT,
        CONSTRAINT FK_User_Customer FOREIGN KEY (customer_id) REFERENCES functional.customer (id)
    );
END;

-- Create table "simple_user"
IF OBJECT_ID(N'functional.simple_user', N'U') IS NULL
BEGIN
    DROP TABLE IF EXISTS functional.simple_user;
    CREATE TABLE functional.simple_user (
        id INT PRIMARY KEY,
        tc_creation_src NVARCHAR(MAX),
        tc_creation DATETIME NOT NULL,
        tc_update_src NVARCHAR(MAX),
        tc_update DATETIME,
        full_name NVARCHAR(MAX),
        email NVARCHAR(MAX) NOT NULL,
        hashed_password NVARCHAR(MAX) NOT NULL,
        active BIT,
        superuser BIT,
        language NVARCHAR(MAX)
    );
END;
