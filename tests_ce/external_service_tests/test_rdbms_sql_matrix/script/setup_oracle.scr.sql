DECLARE
    n NUMBER;
BEGIN
    FOR t IN (SELECT table_name FROM user_tables
              WHERE table_name IN ('MATRIX_ROWS', 'MATRIX_ROWS_PK', 'MATRIX_ROWS_CPK', 'MATRIX_SCRIPT')) LOOP
        EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS';
    END LOOP;
END;

-- rows inserted out of (grp, id) order: a read without a deterministic order returns physical order
CREATE TABLE matrix_rows (grp INT, id INT);
CREATE TABLE matrix_rows_pk (grp INT, id INT PRIMARY KEY);
CREATE TABLE matrix_rows_cpk (grp INT, id INT, PRIMARY KEY (grp, id));
CREATE TABLE matrix_script (id INT, note VARCHAR2(40));

INSERT INTO matrix_rows (grp, id) VALUES (2,12);
INSERT INTO matrix_rows (grp, id) VALUES (1,11);
INSERT INTO matrix_rows (grp, id) VALUES (3,10);
INSERT INTO matrix_rows (grp, id) VALUES (2,9);
INSERT INTO matrix_rows (grp, id) VALUES (1,8);
INSERT INTO matrix_rows (grp, id) VALUES (3,7);
INSERT INTO matrix_rows (grp, id) VALUES (2,6);
INSERT INTO matrix_rows (grp, id) VALUES (1,5);
INSERT INTO matrix_rows (grp, id) VALUES (3,4);
INSERT INTO matrix_rows (grp, id) VALUES (2,3);
INSERT INTO matrix_rows (grp, id) VALUES (1,2);
INSERT INTO matrix_rows (grp, id) VALUES (3,1);
INSERT INTO matrix_rows_pk (grp, id) VALUES (2,12);
INSERT INTO matrix_rows_pk (grp, id) VALUES (1,11);
INSERT INTO matrix_rows_pk (grp, id) VALUES (3,10);
INSERT INTO matrix_rows_pk (grp, id) VALUES (2,9);
INSERT INTO matrix_rows_pk (grp, id) VALUES (1,8);
INSERT INTO matrix_rows_pk (grp, id) VALUES (3,7);
INSERT INTO matrix_rows_pk (grp, id) VALUES (2,6);
INSERT INTO matrix_rows_pk (grp, id) VALUES (1,5);
INSERT INTO matrix_rows_pk (grp, id) VALUES (3,4);
INSERT INTO matrix_rows_pk (grp, id) VALUES (2,3);
INSERT INTO matrix_rows_pk (grp, id) VALUES (1,2);
INSERT INTO matrix_rows_pk (grp, id) VALUES (3,1);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (2,12);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (1,11);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (3,10);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (2,9);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (1,8);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (3,7);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (2,6);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (1,5);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (3,4);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (2,3);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (1,2);
INSERT INTO matrix_rows_cpk (grp, id) VALUES (3,1);

-- a comment; with a semicolon
/* a block comment; with a semicolon */
INSERT INTO matrix_script (id, note) VALUES (1, 'a;b');
INSERT INTO matrix_script (id, note) VALUES (2, 'x -- y');
INSERT INTO matrix_script (id, note) VALUES (3, 'p /* q */ r');
INSERT INTO matrix_script (id, note) VALUES (6, '100% :done');

-- PL/SQL block with IF / END IF and a CASE expression: must stay one statement
DECLARE
    n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM matrix_script WHERE note = 'a;b';
    IF n = 1 THEN
        INSERT INTO matrix_script (id, note) VALUES (4, CASE WHEN n > 0 THEN 'plsql' ELSE 'none' END);
    END IF;
END;

-- trigger body with its own semicolons: must stay one statement
CREATE OR REPLACE TRIGGER matrix_script_note BEFORE INSERT ON matrix_script FOR EACH ROW
BEGIN
    IF :new.note IS NULL THEN
        :new.note := 'trigger';
    END IF;
END;

INSERT INTO matrix_script (id, note) VALUES (5, NULL);
