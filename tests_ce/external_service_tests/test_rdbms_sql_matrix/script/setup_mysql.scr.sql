DROP TABLE IF EXISTS matrix_rows;
DROP TABLE IF EXISTS matrix_rows_pk;
DROP TABLE IF EXISTS matrix_rows_cpk;
DROP TABLE IF EXISTS matrix_script;

-- rows inserted out of (grp, id) order: a read without a deterministic order returns physical order
CREATE TABLE matrix_rows (grp INT, id INT);
CREATE TABLE matrix_rows_pk (grp INT, id INT PRIMARY KEY);
CREATE TABLE matrix_rows_cpk (grp INT, id INT, PRIMARY KEY (grp, id));
CREATE TABLE matrix_script (id INT, note VARCHAR(40));

INSERT INTO matrix_rows (grp, id) VALUES (2, 12), (1, 11), (3, 10), (2, 9), (1, 8), (3, 7), (2, 6), (1, 5), (3, 4), (2, 3), (1, 2), (3, 1);
INSERT INTO matrix_rows_pk (grp, id) VALUES (2, 12), (1, 11), (3, 10), (2, 9), (1, 8), (3, 7), (2, 6), (1, 5), (3, 4), (2, 3), (1, 2), (3, 1);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (2, 12), (1, 11), (3, 10), (2, 9), (1, 8), (3, 7), (2, 6), (1, 5), (3, 4), (2, 3), (1, 2), (3, 1);

-- a comment; with a semicolon
/* a block comment; with a semicolon */
INSERT INTO matrix_script (id, note) VALUES (1, 'a;b');
INSERT INTO matrix_script (id, note) VALUES (2, 'x -- y');
INSERT INTO matrix_script (id, note) VALUES (3, 'p /* q */ r');
INSERT INTO matrix_script (id, note) VALUES (6, '100% :done');
INSERT INTO matrix_script (id, note) VALUES (4, 'plsql');
INSERT INTO matrix_script (id, note) VALUES (5, 'trigger');
