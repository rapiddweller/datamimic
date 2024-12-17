USE master;


-- Check if 'simple' schema exists
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'simple')
BEGIN
    EXEC('CREATE SCHEMA simple');
END

-- Drop tables if they exist
DROP TABLE IF EXISTS simple.cpu_measure;

-- Check if 'cpu_measure' table exists in the 'simple' schema
IF OBJECT_ID(N'simple.cpu_measure', N'U') IS NULL
BEGIN
    -- Create the "cpu_measure" table in the 'simple' schema
    CREATE TABLE simple.cpu_measure (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tc_creation_src NVARCHAR(255),
        tc_creation DATETIME2 NOT NULL,
        tc_update_src NVARCHAR(255),
        tc_update DATETIME2,
        no NVARCHAR(20) NOT NULL,
        name NVARCHAR(100),
        active BIT NOT NULL,
        CONSTRAINT UQ_cpu_measure_id UNIQUE (id)
    );
END