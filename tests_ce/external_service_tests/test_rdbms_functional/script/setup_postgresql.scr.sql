-- Check if 'functional' schema exists
CREATE SCHEMA IF NOT EXISTS functional;

-- Drop tables if they exist
DROP TABLE IF EXISTS functional."user";
DROP TABLE IF EXISTS functional.customer;
DROP TABLE IF EXISTS functional.simple_user;

-- Create table "customer"
CREATE TABLE IF NOT EXISTS functional.customer (
    id SERIAL PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tc_update_src TEXT,
    tc_update TIMESTAMP,
    no TEXT NOT NULL,
    name TEXT,
    active BOOLEAN NOT NULL
);

-- Create table "user"
CREATE TABLE IF NOT EXISTS functional."user" (
    id SERIAL PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tc_update_src TEXT,
    tc_update TIMESTAMP,
    full_name TEXT,
    email TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    active BOOLEAN,
    superuser BOOLEAN,
    language TEXT,
    customer_id INT,
    FOREIGN KEY (customer_id) REFERENCES functional.customer(id)
);

-- Create table "simple_user"
CREATE TABLE IF NOT EXISTS functional.simple_user (
    id SERIAL PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tc_update_src TEXT,
    tc_update TIMESTAMP,
    full_name TEXT,
    email TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    active BOOLEAN,
    superuser BOOLEAN,
    language TEXT
);
