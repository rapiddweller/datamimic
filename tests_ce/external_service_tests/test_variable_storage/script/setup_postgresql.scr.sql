CREATE SCHEMA IF NOT EXISTS simple;

DROP TABLE IF EXISTS simple.storage_pool;

CREATE TABLE simple.storage_pool (
    row_id INT PRIMARY KEY,
    text TEXT
);

INSERT INTO simple.storage_pool (row_id, text)
SELECT g, 'Name ' || g FROM generate_series(1, 15) AS g;

-- Deliberately has DUPLICATE rows once id is excluded from the read (5 distinct categories,
-- each repeated 3x) - storage="iterator" unique="true" against a source with no primary key on
-- the exposed columns, so a passing test proves the dedup actually collapses repeats, not just
-- that it leaves an already-distinct pool alone (row_id-keyed tables can never contain a real
-- duplicate row, so a unique= test against one wouldn't exercise dedup at all).
DROP TABLE IF EXISTS simple.storage_pool_dupes;

CREATE TABLE simple.storage_pool_dupes (
    id SERIAL PRIMARY KEY,
    category TEXT
);

INSERT INTO simple.storage_pool_dupes (category)
SELECT unnest(array_fill(cat, ARRAY[3]))
FROM unnest(ARRAY['A', 'B', 'C', 'D', 'E']) AS cat;
