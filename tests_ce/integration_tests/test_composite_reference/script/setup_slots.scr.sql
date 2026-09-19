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
-- Sparse composite key, NOT a full grid. EU codes are E1/E2, US codes are U1/U2/U3.
-- An independent per-column generator could invent EU+U1, a row that does not exist.
-- Tuple-integrity generation only ever emits these 5 real pairs (the core composite-FK property).
-- (Keep this comment free of the semicolon char: the script splits commands on it.)
DROP TABLE IF EXISTS region_codes;
CREATE TABLE region_codes (region TEXT, code TEXT);
INSERT INTO region_codes VALUES ('EU', 'E1');
INSERT INTO region_codes VALUES ('EU', 'E2');
INSERT INTO region_codes VALUES ('US', 'U1');
INSERT INTO region_codes VALUES ('US', 'U2');
INSERT INTO region_codes VALUES ('US', 'U3');
