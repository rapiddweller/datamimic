-- reference-distribution fixture: 4 rows, stable fetch order = ORDER BY id -> 1,2,3,4.
DROP TABLE IF EXISTS items;
CREATE TABLE items (id INTEGER);
INSERT INTO items (id) VALUES (3);
INSERT INTO items (id) VALUES (1);
INSERT INTO items (id) VALUES (4);
INSERT INTO items (id) VALUES (2);
