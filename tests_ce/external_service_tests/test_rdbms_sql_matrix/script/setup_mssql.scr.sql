USE master

IF OBJECT_ID(N'matrix_script_note', N'TR') IS NOT NULL
    DROP TRIGGER matrix_script_note;
DROP TABLE IF EXISTS matrix_rows;
DROP TABLE IF EXISTS matrix_rows_pk;
DROP TABLE IF EXISTS matrix_rows_cpk;
DROP TABLE IF EXISTS matrix_script;

-- rows inserted out of (grp, id) order: a read without a deterministic order returns physical order
CREATE TABLE matrix_rows (grp INT, id INT);
CREATE TABLE matrix_rows_pk (grp INT, id INT PRIMARY KEY);
CREATE TABLE matrix_rows_cpk (grp INT, id INT, PRIMARY KEY (grp, id));
CREATE TABLE matrix_script (id INT, note NVARCHAR(40));

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

EXEC(N'CREATE TRIGGER matrix_script_note ON matrix_script AFTER INSERT AS
BEGIN
    UPDATE target SET note = ''trigger''
    FROM matrix_script AS target
    INNER JOIN inserted AS row_data ON target.id = row_data.id
    WHERE row_data.note IS NULL;
END');

INSERT INTO matrix_script (id, note) VALUES (5, NULL);
