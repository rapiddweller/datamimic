USE master

-- Check if 'functional' schema exists
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'functional')
BEGIN
    EXEC('CREATE SCHEMA functional');
END;

-- Drop tables if they exist
DROP TABLE IF EXISTS functional.sequence_table_generator;

DROP SEQUENCE IF EXISTS example_sequence;

CREATE SEQUENCE example_sequence
    START WITH 1
    INCREMENT BY 1;

-- Create table "customer"
IF OBJECT_ID(N'functional.sequence_table_generator', N'U') IS NULL
BEGIN
    CREATE TABLE functional.sequence_table_generator (
        id INT DEFAULT NEXT VALUE FOR example_sequence PRIMARY KEY,
        name NVARCHAR(MAX)
    );
END;
