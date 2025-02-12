-- Check if 'functional' schema exists
CREATE SCHEMA IF NOT EXISTS functional;

-- Drop tables if they exist
DROP TABLE IF EXISTS functional."sequence_table_generator";

-- Create table "sequence_table_generator"
CREATE TABLE IF NOT EXISTS functional."sequence_table_generator" (
    id SERIAL PRIMARY KEY,
    name TEXT
);

