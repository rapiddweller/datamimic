-- Check if 'functional' schema exists and create it if not
CREATE DATABASE IF NOT EXISTS functional;

-- Use the 'functional' schema
USE functional;

-- Drop tables if they exist
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS simple_user;

-- Create table "customer"
CREATE TABLE IF NOT EXISTS customer (
    id INT PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    no TEXT NOT NULL,
    name TEXT,
    active TINYINT(1) NOT NULL
);

-- Create table "user"
CREATE TABLE IF NOT EXISTS user (
    id INT PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    full_name TEXT,
    email TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    active TINYINT(1),
    superuser TINYINT(1),
    language TEXT,
    customer_id INT,
    FOREIGN KEY (customer_id) REFERENCES customer(id)
);

-- Create table "simple_user"
CREATE TABLE IF NOT EXISTS simple_user (
    id INT PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    full_name TEXT,
    email TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    active TINYINT(1),
    superuser TINYINT(1),
    language TEXT
);
