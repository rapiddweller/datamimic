# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""sql_dialect: a page keeps the selector's own ORDER BY first and breaks its ties with the remaining
output columns (#228); scripts split only at statement-ending semicolons. Pure SQL text handling without
a database, so a Python test; paging and script execution against real databases are covered by the DSL
models in tests_ce/external_service_tests/test_rdbms_sql_matrix."""

import pytest

from datamimic_ce.engine.dsl.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.clients.sql_dialect import SelectorPage, selector_page, split_script

_COLUMNS = ["grp", "id"]
_DB_PAGED = slice(None)


@pytest.mark.parametrize(
    ("dbms", "query", "sql", "rows"),
    [
        (Dbms.POSTGRESQL, "SELECT grp, id FROM t", "SELECT grp, id FROM t ORDER BY 1, 2 LIMIT 5 OFFSET 10", _DB_PAGED),
        (
            Dbms.POSTGRESQL,
            "SELECT grp, id FROM t ORDER BY grp",
            "SELECT grp, id FROM t ORDER BY grp, 2 LIMIT 5 OFFSET 10",
            _DB_PAGED,
        ),
        (
            Dbms.MSSQL,
            "SELECT grp, id FROM t ORDER BY id DESC;",
            "SELECT grp, id FROM t ORDER BY id DESC, 1 OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY",
            _DB_PAGED,
        ),
        (
            Dbms.ORACLE,
            "SELECT grp, id FROM t ORDER BY 2, 1 -- all columns",
            "SELECT grp, id FROM t ORDER BY 2, 1 OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY",
            _DB_PAGED,
        ),
        (
            Dbms.MSSQL,
            "SELECT g AS grp, id FROM t ORDER BY g",
            "SELECT g AS grp, id FROM t ORDER BY g, 2 OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY",
            _DB_PAGED,
        ),
        (
            Dbms.MSSQL,
            "SELECT a.id AS a_id, b.id AS b_id FROM t a JOIN t b ON a.grp = b.grp ORDER BY a.id",
            "SELECT a.id AS a_id, b.id AS b_id FROM t a JOIN t b ON a.grp = b.grp ORDER BY a.id, 2 "
            "OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY",
            _DB_PAGED,
        ),
        (
            Dbms.POSTGRESQL,
            "SELECT a.id AS a_id, b.id AS b_id FROM t a JOIN t b ON a.grp = b.grp ORDER BY b_id",
            "SELECT a.id AS a_id, b.id AS b_id FROM t a JOIN t b ON a.grp = b.grp ORDER BY b_id, 1 LIMIT 5 OFFSET 10",
            _DB_PAGED,
        ),
        (
            Dbms.MSSQL,
            "SELECT id AS i, grp FROM t ORDER BY t.id",
            "SELECT id AS i, grp FROM t ORDER BY t.id, 2 OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY",
            _DB_PAGED,
        ),
        (
            Dbms.MSSQL,
            "SELECT * FROM t ORDER BY t.grp",
            "SELECT * FROM t ORDER BY t.grp, 2 OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY",
            _DB_PAGED,
        ),
        (
            Dbms.POSTGRESQL,
            "SELECT grp, id FROM t ORDER BY LOWER(grp)",
            "SELECT grp, id FROM t ORDER BY LOWER(grp), 1, 2 LIMIT 5 OFFSET 10",
            _DB_PAGED,
        ),
        (
            Dbms.POSTGRESQL,
            "SELECT grp, ROW_NUMBER() OVER (ORDER BY grp) AS id FROM t",
            "SELECT grp, ROW_NUMBER() OVER (ORDER BY grp) AS id FROM t ORDER BY 1, 2 LIMIT 5 OFFSET 10",
            _DB_PAGED,
        ),
        (
            Dbms.POSTGRESQL,
            "SELECT * FROM (SELECT grp, id FROM t ORDER BY id LIMIT 3) AS s",
            "SELECT * FROM (SELECT grp, id FROM t ORDER BY id LIMIT 3) AS s ORDER BY 1, 2 LIMIT 5 OFFSET 10",
            _DB_PAGED,
        ),
        (
            Dbms.MSSQL,
            "SELECT grp, id FROM t UNION SELECT grp, id FROM u ORDER BY grp",
            "SELECT grp, id FROM t UNION SELECT grp, id FROM u ORDER BY grp, 2 OFFSET 10 ROWS FETCH NEXT 5 ROWS ONLY",
            _DB_PAGED,
        ),
        (
            Dbms.POSTGRESQL,
            "SELECT grp, id FROM t ORDER BY grp DESC LIMIT 7",
            "SELECT grp, id FROM t ORDER BY grp DESC, 2 LIMIT 7",
            slice(10, 15),
        ),
        (
            Dbms.POSTGRESQL,
            "SELECT grp, id FROM t OFFSET 5 LIMIT 10",
            "SELECT grp, id FROM t ORDER BY 1, 2 OFFSET 5 LIMIT 10",
            slice(10, 15),
        ),
        (Dbms.MYSQL, "SELECT grp, id FROM t LIMIT 7", "SELECT grp, id FROM t ORDER BY 1, 2 LIMIT 7", slice(10, 15)),
        (
            Dbms.MSSQL,
            "SELECT TOP 7 grp, id FROM t ORDER BY grp",
            "SELECT TOP 7 grp, id FROM t ORDER BY grp, 2",
            slice(10, 15),
        ),
        (
            Dbms.ORACLE,
            "SELECT grp, id FROM t ORDER BY grp FETCH FIRST 7 ROWS ONLY",
            "SELECT grp, id FROM t ORDER BY grp, 2 FETCH FIRST 7 ROWS ONLY",
            slice(10, 15),
        ),
        (
            Dbms.POSTGRESQL,
            "SELEC nonsense ((",
            "SELECT * FROM (SELEC nonsense (() AS original_query ORDER BY 1, 2 LIMIT 5 OFFSET 10",
            _DB_PAGED,
        ),
    ],
)
def test_selector_page_keeps_own_order_first_and_breaks_ties(dbms: Dbms, query: str, sql: str, rows: slice) -> None:
    """A selector with its own row limit is a bounded result: ordered deterministically inside its limit,
    read whole and paged in Python, so its own order survives."""
    assert selector_page(query, dbms, 10, 5, _COLUMNS) == SelectorPage(sql, rows)


_ORACLE_SCRIPT = """-- drop; if present
DECLARE
    n NUMBER;
BEGIN
    SELECT COUNT(*) INTO n FROM user_tables WHERE table_name = 'A;B';
    IF n > 0 THEN
        EXECUTE IMMEDIATE 'DROP TABLE A';
    END IF;
    n := CASE WHEN n > 1 THEN 1 END;
END;
/* comment; */ CREATE TABLE begin_date (id INT);
CREATE OR REPLACE TRIGGER t BEFORE INSERT ON begin_date FOR EACH ROW BEGIN :new.id := 1; END;
INSERT INTO begin_date VALUES (1);"""


def test_split_script_oracle_keeps_plsql_blocks_whole() -> None:
    statements = split_script(_ORACLE_SCRIPT, Dbms.ORACLE)
    assert len(statements) == 4
    assert statements[0].startswith("DECLARE") and statements[0].endswith("END;")
    assert "'A;B'" in statements[0] and "END IF;" in statements[0]
    assert statements[1] == "CREATE TABLE begin_date (id INT)"
    assert statements[2].startswith("CREATE OR REPLACE TRIGGER") and statements[2].endswith("END;")
    assert statements[3] == "INSERT INTO begin_date VALUES (1)"


@pytest.mark.parametrize("dbms", [Dbms.SQLITE, Dbms.MYSQL])
def test_split_script_ignores_semicolons_in_literals_and_comments(dbms: Dbms) -> None:
    script = "CREATE TABLE t (v TEXT); -- a; comment\nINSERT INTO t VALUES ('x;y');\n/* ; */"
    assert split_script(script, dbms) == ["CREATE TABLE t (v TEXT)", "INSERT INTO t VALUES ('x;y')"]


def test_split_script_keeps_sqlite_trigger_body_whole() -> None:
    script = "CREATE TRIGGER t AFTER INSERT ON x BEGIN UPDATE y SET n = n + 1; END; INSERT INTO x VALUES (1);"
    assert split_script(script, Dbms.SQLITE) == [
        "CREATE TRIGGER t AFTER INSERT ON x BEGIN UPDATE y SET n = n + 1; END;",
        "INSERT INTO x VALUES (1)",
    ]


@pytest.mark.parametrize(
    ("script", "statements"),
    [
        ("BEGIN; CREATE TABLE t (id INT);", ["BEGIN", "CREATE TABLE t (id INT)"]),
        ("BEGIN TRANSACTION; CREATE TABLE t (id INT);", ["BEGIN TRANSACTION", "CREATE TABLE t (id INT)"]),
    ],
)
def test_split_script_does_not_treat_sqlite_transactions_as_compound_blocks(
    script: str, statements: list[str]
) -> None:
    assert split_script(script, Dbms.SQLITE) == statements


@pytest.mark.parametrize(
    "statement",
    [
        "CREATE TRIGGER t BEFORE INSERT ON x FOR EACH ROW BEGIN SET @a = 1; SET @b = 2; END;",
        "CREATE PROCEDURE p() BEGIN SELECT 1; SELECT 2; END;",
        "CREATE FUNCTION f() RETURNS INT BEGIN RETURN 1; END;",
        "CREATE EVENT e ON SCHEDULE EVERY 1 DAY DO BEGIN INSERT INTO t VALUES (1); END;",
    ],
)
def test_split_script_keeps_mysql_compound_create_body_whole(statement: str) -> None:
    assert split_script(f"{statement} INSERT INTO t VALUES (3);", Dbms.MYSQL) == [
        statement,
        "INSERT INTO t VALUES (3)",
    ]


@pytest.mark.parametrize(
    "loop_body",
    [
        "WHILE NEW.id < 2 DO SET NEW.id = NEW.id + 1; END WHILE;",
        "REPEAT SET NEW.id = NEW.id + 1; UNTIL NEW.id >= 2 END REPEAT;",
    ],
)
def test_split_script_keeps_mysql_trigger_loops_inside_outer_begin(loop_body: str) -> None:
    statement = f"CREATE TRIGGER t BEFORE INSERT ON x FOR EACH ROW BEGIN {loop_body} END;"
    assert split_script(f"{statement} INSERT INTO x VALUES (1);", Dbms.MYSQL) == [
        statement,
        "INSERT INTO x VALUES (1)",
    ]


def test_split_script_rejects_mysql_client_delimiter_directive() -> None:
    assert split_script("SELECT 'DELIMITER';", Dbms.MYSQL) == ["SELECT 'DELIMITER'"]
    assert split_script("SELECT delimiter FROM t;", Dbms.MYSQL) == ["SELECT delimiter FROM t"]
    with pytest.raises(ValueError, match="DELIMITER directives"):
        split_script("DELIMITER //\nCREATE PROCEDURE p() BEGIN SELECT 1; END//", Dbms.MYSQL)


def test_split_script_does_not_treat_plain_create_table_identifiers_as_compound() -> None:
    script = "CREATE TABLE t (trigger TEXT, begin TEXT); INSERT INTO t VALUES ('x', 'y');"
    assert split_script(script, Dbms.SQLITE) == [
        "CREATE TABLE t (trigger TEXT, begin TEXT)",
        "INSERT INTO t VALUES ('x', 'y')",
    ]


@pytest.mark.parametrize("dbms", [Dbms.POSTGRESQL, Dbms.MSSQL])
def test_split_script_passes_batches_through(dbms: Dbms) -> None:
    script = "CREATE TABLE t (v INT); INSERT INTO t VALUES (1);"
    assert split_script(script, dbms) == [script]
