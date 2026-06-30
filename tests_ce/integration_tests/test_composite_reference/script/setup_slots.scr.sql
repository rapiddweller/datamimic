-- composite-reference fixture: (aisle, bin) with mixed types (TEXT, INTEGER) + duplicate combos.
DROP TABLE IF EXISTS slots;
CREATE TABLE IF NOT EXISTS slots (aisle TEXT, bin INTEGER);
INSERT INTO slots (aisle, bin) VALUES ('A', 1);
INSERT INTO slots (aisle, bin) VALUES ('A', 2);
INSERT INTO slots (aisle, bin) VALUES ('B', 1);
INSERT INTO slots (aisle, bin) VALUES ('B', 2);
INSERT INTO slots (aisle, bin) VALUES ('C', 1);
INSERT INTO slots (aisle, bin) VALUES ('C', 2);
INSERT INTO slots (aisle, bin) VALUES ('A', 1);
INSERT INTO slots (aisle, bin) VALUES ('B', 2);
-- 3-column composite with three types (TEXT, INTEGER, REAL): 4 distinct combos.
DROP TABLE IF EXISTS parts;
CREATE TABLE IF NOT EXISTS parts (region TEXT, year INTEGER, price REAL);
INSERT INTO parts (region, year, price) VALUES ('EU', 2023, 1.5);
INSERT INTO parts (region, year, price) VALUES ('EU', 2024, 2.5);
INSERT INTO parts (region, year, price) VALUES ('US', 2023, 3.5);
INSERT INTO parts (region, year, price) VALUES ('US', 2024, 4.5);
INSERT INTO parts (region, year, price) VALUES ('EU', 2023, 1.5);
