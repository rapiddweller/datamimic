-- IMPORTANT: Only use semicolon for commands split when using SQLite
-- Setup table for source-read determinism tests.
DROP TABLE IF EXISTS det_items;
CREATE TABLE IF NOT EXISTS det_items (
    id INTEGER PRIMARY KEY,
    label TEXT NOT NULL
);
INSERT INTO det_items (id, label) VALUES (0, 'item_0');
INSERT INTO det_items (id, label) VALUES (1, 'item_1');
INSERT INTO det_items (id, label) VALUES (2, 'item_2');
INSERT INTO det_items (id, label) VALUES (3, 'item_3');
INSERT INTO det_items (id, label) VALUES (4, 'item_4');
INSERT INTO det_items (id, label) VALUES (5, 'item_5');
INSERT INTO det_items (id, label) VALUES (6, 'item_6');
INSERT INTO det_items (id, label) VALUES (7, 'item_7');
INSERT INTO det_items (id, label) VALUES (8, 'item_8');
INSERT INTO det_items (id, label) VALUES (9, 'item_9');
INSERT INTO det_items (id, label) VALUES (10, 'item_10');
INSERT INTO det_items (id, label) VALUES (11, 'item_11');
