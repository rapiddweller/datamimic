-- IMPORTANT: Only use semicolon for commands split when using SQLite
-- Drop the referencing table before customer when resetting existing data.
DROP TABLE IF EXISTS "user";

-- Create the "customer" table
DROP TABLE IF EXISTS customer;
CREATE TABLE IF NOT EXISTS customer (
    id INTEGER PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src TEXT,
    tc_update TIMESTAMP,
    no TEXT NOT NULL,
    name TEXT,
    UNIQUE (id)
);

-- Create the "product" table
DROP TABLE IF EXISTS product;
CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src TEXT,
    tc_update TIMESTAMP,
    active BOOLEAN NOT NULL,
    name TEXT,
    description TEXT,
    img_links TEXT,
    shop_link TEXT,
    no TEXT NOT NULL,
    UNIQUE (id)
);

-- Create the "user" table
CREATE TABLE IF NOT EXISTS "user" (
    id INTEGER PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src TEXT,
    tc_update TIMESTAMP,
    full_name TEXT,
    email TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    active BOOLEAN,
    superuser BOOLEAN,
    language TEXT,
    customer_id INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customer (id)
);
