USE master

IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = N'functional')
BEGIN
    EXEC('CREATE SCHEMA functional');
END;

DROP TABLE IF EXISTS functional.page_rows;
DROP TABLE IF EXISTS functional.page_rows_pk;

-- no key; first column grp is not unique, so the old ORDER BY 1 left ties unordered
CREATE TABLE functional.page_rows (grp INT, id INT);
-- primary key is not the first column
CREATE TABLE functional.page_rows_pk (grp INT, id INT PRIMARY KEY);

INSERT INTO functional.page_rows (grp, id) VALUES (2, 12), (1, 11), (3, 10), (2, 9), (1, 8), (3, 7), (2, 6), (1, 5), (3, 4), (2, 3), (1, 2), (3, 1);
INSERT INTO functional.page_rows_pk (grp, id) VALUES (2, 12), (1, 11), (3, 10), (2, 9), (1, 8), (3, 7), (2, 6), (1, 5), (3, 4), (2, 3), (1, 2), (3, 1);
