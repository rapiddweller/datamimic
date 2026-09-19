CREATE SCHEMA IF NOT EXISTS functional;

DROP TABLE IF EXISTS functional.page_rows;
DROP TABLE IF EXISTS functional.page_rows_pk;

-- no key; first column grp is not unique
CREATE TABLE functional.page_rows (grp INT, id INT);
-- primary key is not the first column
CREATE TABLE functional.page_rows_pk (grp INT, id INT PRIMARY KEY);

-- inserted out of (grp, id) order: an unordered page read returns physical order, not key order
INSERT INTO functional.page_rows (grp, id) VALUES (2, 12), (1, 11), (3, 10), (2, 9), (1, 8), (3, 7), (2, 6), (1, 5), (3, 4), (2, 3), (1, 2), (3, 1);
INSERT INTO functional.page_rows_pk (grp, id) VALUES (2, 12), (1, 11), (3, 10), (2, 9), (1, 8), (3, 7), (2, 6), (1, 5), (3, 4), (2, 3), (1, 2), (3, 1);
