# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""sql_dialect: a page keeps the selector's own ORDER BY first and breaks its ties with the remaining
output columns (#228); scripts split only at statement-ending semicolons. Pure SQL text handling without
a database, so a Python test; paging and script execution against real databases are covered by the DSL
models in tests_ce/external_service_tests/test_rdbms_paging_order."""

import pytest

from datamimic_ce.clients.sql_dialect import SelectorPage, selector_page, split_script
from datamimic_ce.enums.dbms_enums import Dbms

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


@pytest.mark.parametrize("dbms", [Dbms.POSTGRESQL, Dbms.MSSQL])
def test_split_script_passes_batches_through(dbms: Dbms) -> None:
    script = "CREATE TABLE t (v INT); INSERT INTO t VALUES (1);"
    assert split_script(script, dbms) == [script]
