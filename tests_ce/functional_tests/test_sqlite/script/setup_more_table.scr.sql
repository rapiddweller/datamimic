-- IMPORTANT: Only use semicolon for commands split when using SQLite
-- Create the "simple_user" table
DROP TABLE IF EXISTS simple_user;
CREATE TABLE IF NOT EXISTS simple_user (
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
    language TEXT
);
