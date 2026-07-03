import shutil
from pathlib import Path

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _clean():
    shutil.rmtree(_DIR / "db", ignore_errors=True)


def _rows(database: str, table: str) -> int:
    cfg = RdbmsConnectionConfig(dbms="sqlite", database=database, host=None, port=None,
                                user=None, password=None, db_schema=None)
    client = RdbmsClient(cfg, task_id="t")
    return len(client.get(f"SELECT n FROM {table}"))


def test_target_entity_routes_write_to_its_table_not_the_statement_name():
    _clean()
    try:
        DataMimicTest(test_dir=_DIR, filename="target_entity.xml", capture_test_result=True).test_with_timer()
        assert _rows("target_entity_db", "customers") == 3  # targetEntity='customers' overrode name='gen'
    finally:
        _clean()


def test_source_entity_routes_read_to_its_table_not_the_statement_name():
    _clean()
    try:
        engine = DataMimicTest(test_dir=_DIR, filename="source_entity.xml", capture_test_result=True)
        engine.test_with_timer()
        rows = engine.capture_result()["reader"]
        assert sorted(r["n"] for r in rows) == [1, 2, 3, 4]  # sourceEntity='people' read the seeded table
    finally:
        _clean()


def test_backward_compat_type_still_routes_the_write_without_target_entity():
    _clean()
    try:
        DataMimicTest(test_dir=_DIR, filename="backward_compat.xml", capture_test_result=True).test_with_timer()
        assert _rows("bc_db", "orders") == 2  # existing 'type'-routes-write behaviour unchanged
    finally:
        _clean()


def test_blank_target_entity_is_a_validation_error():
    import pytest

    with pytest.raises(Exception, match=r"must not be blank"):
        DataMimicTest(test_dir=_DIR, filename="blank_entity.xml", capture_test_result=True).test_with_timer()
