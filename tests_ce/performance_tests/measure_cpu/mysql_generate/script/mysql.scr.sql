CREATE DATABASE IF NOT EXISTS simple;

DROP TABLE IF EXISTS simple.cpu_measure;

-- Create the "simple.cpu_measure" table
CREATE TABLE simple.cpu_measure (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    no TEXT NOT NULL,
    name TEXT,
    active BOOLEAN NOT NULL
);
