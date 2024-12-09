-- Check if 'functional' schema exists
CREATE SCHEMA IF NOT EXISTS functional;

-- Drop tables if they exist
DROP TABLE IF EXISTS functional."motorcycles";

-- Create table "motorcycles"
CREATE TABLE IF NOT EXISTS functional.motorcycles (
    id SERIAL PRIMARY KEY,
    year INT
);

