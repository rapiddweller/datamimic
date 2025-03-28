-- IMPORTANT: Only use semicolon for commands split when using SQLite
-- Create the "customer" table
DROP TABLE IF EXISTS customer;
CREATE TABLE IF NOT EXISTS customer (
    id INTEGER PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    no TEXT NOT NULL,
    name TEXT,
    active BOOLEAN NOT NULL,
    UNIQUE (id)
);

-- Create the "user" table
DROP TABLE IF EXISTS user;
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    full_name TEXT,
    email TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    active BOOLEAN,
    superuser BOOLEAN,
    language TEXT,
    customer_id INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customer (id)
);
