CREATE SCHEMA IF NOT EXISTS simple;

DROP TABLE IF EXISTS simple.storage_pool;

CREATE TABLE simple.storage_pool (
    row_id INT PRIMARY KEY,
    text TEXT
);

INSERT INTO simple.storage_pool (row_id, text)
SELECT g, 'Name ' || g FROM generate_series(1, 15) AS g;
