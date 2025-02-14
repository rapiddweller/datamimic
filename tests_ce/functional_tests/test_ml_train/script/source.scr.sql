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
    UNIQUE (id)
);
