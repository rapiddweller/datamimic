# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""RDBMS SQL matrix (#228): the same DSL cases (matrix_cases.xml) run end-to-end on every engine and must give
the same rows. Covers deterministic paging of table sources and selectors (own ORDER BY, ties, aliases, unions,
bounded selectors), the variable count path, <execute> script splitting, and dbms validation."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Event
from uuid import uuid4

import pytest
from sqlalchemy import event
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql.elements import TextClause

from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms
from datamimic_ce.engine.io.api import ColumnKind, load_connection_profile
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_TEST_DIR = Path(__file__).resolve().parent
_ENGINES = ["postgresql", "mssql", "oracle", "mysql", "sqlite"]

_BY_GRP_ID = [(1, 2), (1, 5), (1, 8), (1, 11), (2, 3), (2, 6), (2, 9), (2, 12), (3, 1), (3, 4), (3, 7), (3, 10)]
_BY_ID = sorted(_BY_GRP_ID, key=lambda row: row[1])
_BY_GRP_DESC_ID = sorted(_BY_GRP_ID, key=lambda row: (-row[0], row[1]))

_EXACT_ORDER = {
    "table_keyless": _BY_GRP_ID,
    "table_pk": _BY_ID,
    "table_composite_pk": _BY_GRP_ID,
    "selector_unordered": _BY_GRP_ID,
    "selector_window": _BY_GRP_ID,
    "selector_unique_order": _BY_ID[::-1],
    "selector_tied_order": _BY_GRP_ID,
    "selector_star_order": _BY_GRP_ID,
    "selector_union_order": [row for row in _BY_GRP_DESC_ID if row[0] != 2],
    "selector_terminated": _BY_ID,
    "selector_bounded_ordered": _BY_GRP_DESC_ID[:7],
    "selector_bounded_unordered": _BY_GRP_ID[:7],
}
_EVERY_ROW_ONCE = ["table_keyless_mp", "table_random_mp", "selector_unordered_mp", "selector_tied_order_mp"]


def _grp_id(rows: list[dict], grp_key: str = "grp") -> list[tuple[int, int]]:
    return [(row[grp_key], row["id"]) for row in rows]


@pytest.mark.parametrize("engine", _ENGINES)
def test_rdbms_sql_matrix(engine: str) -> None:
    test_engine = DataMimicTest(test_dir=_TEST_DIR, filename=f"matrix_{engine}.xml", capture_test_result=True)
    test_engine.test_with_timer()
    result = test_engine.capture_result()

    for product, expected in _EXACT_ORDER.items():
        assert _grp_id(result[product]) == expected, product
    for product in _EVERY_ROW_ONCE:
        assert sorted(_grp_id(result[product])) == _BY_GRP_ID, product

    assert all(row["rn"] == row["id"] for row in result["selector_window"])
    assert _grp_id(result["selector_alias_order"], grp_key="g") == _BY_GRP_DESC_ID
    # a.id repeats once per same-grp b row (4x), so pages of 5 split a.id groups: b.id must break those ties
    same_grp_pairs = sorted((a_id, b_id) for grp, a_id in _BY_GRP_ID for other, b_id in _BY_GRP_ID if grp == other)
    assert [(row["a_id"], row["b_id"]) for row in result["selector_qualified_order"]] == same_grp_pairs
    assert [row["id"] for row in result["variable_selector_cyclic"]] == [*range(12, 0, -1), 12, 11, 10]
    expected_cyclic_ids = [row[1] for row in _BY_GRP_ID]
    expected_cyclic_ids *= 2
    expected_cyclic_ids += [2, 5, 8, 11, 3, 6]
    cyclic_ids = [row["id"] for row in result["variable_selector_cyclic_unordered_mp"]]
    assert cyclic_ids == expected_cyclic_ids
    repeat_engine = DataMimicTest(test_dir=_TEST_DIR, filename=f"matrix_{engine}.xml", capture_test_result=True)
    repeat_engine.test_with_timer()
    repeat_result = repeat_engine.capture_result()
    assert [row["id"] for row in repeat_result["variable_selector_cyclic_unordered_mp"]] == cyclic_ids
    assert [(row["id"], row["note"]) for row in result["script_rows"]] == [
        (1, "a;b"),
        (2, "x -- y"),
        (3, "p /* q */ r"),
        (4, "plsql"),
        (5, "trigger"),
        (6, "100% :done"),
    ]


def test_unsupported_dbms_fails_when_the_descriptor_is_read() -> None:
    with pytest.raises(Exception, match="dbms"):
        DataMimicTest(test_dir=_TEST_DIR, filename="invalid_dbms.xml").test_with_timer()


@pytest.mark.parametrize("dbms", [Dbms.POSTGRESQL, Dbms.MYSQL])
def test_overlapping_table_creation(dbms):
    environment = "local" if get_settings().RUNTIME_ENVIRONMENT == "development" else "environment"
    profile = load_connection_profile(_TEST_DIR, environment)
    prefix = dbms.value + ".db."
    config = RdbmsConnectionConfig(
        dbms=dbms,
        host=profile[prefix + "host"],
        port=int(profile[prefix + "port"]),
        database=profile[prefix + "database"],
        user=profile[prefix + "user"],
        password=profile[prefix + "password"],
        db_schema=None,
        # PostgreSQL must open a real transaction for the advisory lock even on an autocommit engine.
        isolation_level="AUTOCOMMIT" if dbms is Dbms.POSTGRESQL else None,
    )
    clients = [RdbmsClient(config), RdbmsClient(config)]
    table = "ce_create_" + uuid4().hex[:16]
    both_reached = Event()
    both_ready = Barrier(2, action=both_reached.set)

    def meet_before_lock_or_create(connection, statement, multiparams, params, execution_options):
        if dbms is Dbms.POSTGRESQL:
            if isinstance(statement, TextClause) and "pg_advisory_xact_lock" in statement.text:
                both_ready.wait(timeout=10)
        elif isinstance(statement, CreateTable):
            both_ready.wait(timeout=10)

    try:
        for client in clients:
            event.listen(client._create_engine(), "before_execute", meet_before_lock_or_create)
        with ThreadPoolExecutor(max_workers=2) as executor:
            columns = (("id", ColumnKind.INTEGER), ("note", ColumnKind.TEXT))
            futures = [executor.submit(client.ensure_table, table, columns, ("id",)) for client in clients]
            for future in futures:
                future.result()
        assert both_reached.is_set()
        for number, client in enumerate(clients):
            client.insert(table, [{"id": number, "note": "created"}])
        assert clients[0].get(f"SELECT id, note FROM {table} ORDER BY id") == [(0, "created"), (1, "created")]
    finally:
        try:
            if clients[0].engine is not None:
                clients[0].execute_sql_script(f"DROP TABLE IF EXISTS {table}")
        finally:
            for client in clients:
                if client.engine is not None:
                    client.engine.dispose()
