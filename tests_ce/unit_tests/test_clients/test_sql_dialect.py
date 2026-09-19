# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""sql_dialect: a top-level ORDER BY is the selector's own source order (#228); scripts split only at
statement-ending semicolons. Pure SQL text handling without a database, so a Python test; paging and
script execution against real databases are covered by the DSL models in
tests_ce/external_service_tests/test_rdbms_paging_order."""

import pytest

from datamimic_ce.clients.sql_dialect import SelectorShape, selector_shape, split_script
from datamimic_ce.enums.dbms_enums import Dbms


@pytest.mark.parametrize(
    ("dbms", "query", "shape"),
    [
        (Dbms.POSTGRESQL, "SELECT id FROM t ORDER BY id DESC", (True, False)),
        (Dbms.POSTGRESQL, "SELECT a, ROW_NUMBER() OVER (ORDER BY a) AS rn FROM t", (False, False)),
        (Dbms.POSTGRESQL, "SELECT * FROM (SELECT a FROM t ORDER BY a LIMIT 3) AS x", (False, False)),
        (Dbms.POSTGRESQL, "SELECT 'order by' AS s FROM t -- order by s", (False, False)),
        (Dbms.POSTGRESQL, "SELECT a FROM t UNION SELECT a FROM u ORDER BY a", (True, False)),
        (Dbms.MYSQL, "SELECT a FROM t ORDER BY a LIMIT 10", (True, True)),
        (Dbms.MSSQL, "SELECT TOP 5 a FROM t ORDER BY a", (True, True)),
        (Dbms.ORACLE, "SELECT a FROM t ORDER BY a FETCH FIRST 3 ROWS ONLY", (True, True)),
        (Dbms.POSTGRESQL, "SELEC nonsense ((", (False, False)),
    ],
)
def test_selector_shape(dbms: Dbms, query: str, shape: tuple[bool, bool]) -> None:
    assert selector_shape(query, dbms) == SelectorShape(*shape)


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
