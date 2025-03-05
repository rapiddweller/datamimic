-- Check if 'functional' schema exists and create it if not
CREATE DATABASE IF NOT EXISTS functional;

-- Use the 'functional' schema
USE functional;

-- Drop tables if they exist
DROP TABLE IF EXISTS sequence_table_generator;

-- Create table "sequence_table_generator"
CREATE TABLE IF NOT EXISTS sequence_table_generator (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name TEXT
);

