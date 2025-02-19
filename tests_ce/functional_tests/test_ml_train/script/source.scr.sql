-- Create the "customer" table
DROP TABLE IF EXISTS customer;
CREATE TABLE IF NOT EXISTS customer (
    id INTEGER PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    no TEXT NOT NULL,
    active BOOL,
    tc_update DATETIME,
    name TEXT,
    UNIQUE (id)
);
