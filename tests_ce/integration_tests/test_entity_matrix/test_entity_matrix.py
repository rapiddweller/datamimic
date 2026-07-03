"""Consistency matrix for sourceEntity / targetEntity across every source and target.

Proves the read/write-entity resolution is applied at the right (single) abstraction point:
- targetEntity routes the WRITE to its physical entity for every target family (store + file).
- sourceEntity routes the READ from its physical entity for every multi-entity source.
The statement name ('gen'/'reader') always differs from the routed entity ('routed'/'seeded'),
so a pass can only mean the entity attribute took effect.
"""

import shutil
from pathlib import Path

import pytest

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.connection_config.rdbms_connection_config import RdbmsConnectionConfig
from datamimic_ce.data_mimic_test import DataMimicTest

_DIR = Path(__file__).resolve().parent


def _clean():
    shutil.rmtree(_DIR / "db", ignore_errors=True)
    shutil.rmtree(_DIR / "output", ignore_errors=True)


def _table_rows(database: str, table: str) -> int:
    cfg = RdbmsConnectionConfig(dbms="sqlite", database=database, host=None, port=None,
                                user=None, password=None, db_schema=None)
    return len(RdbmsClient(cfg, task_id="t").get(f"SELECT n FROM {table}"))


def _run(filename: str) -> DataMimicTest:
    engine = DataMimicTest(test_dir=_DIR, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine


# ---- targetEntity: WRITE routes to the physical entity, not the statement name 'gen' ----

def test_target_entity_rdbms():
    _clean()
    try:
        _run("te_rdbms.xml")
        assert _table_rows("matrix_rdbms", "routed") == 3
    finally:
        _clean()


def test_target_entity_memstore():
    _clean()
    try:
        engine = _run("te_memstore.xml")
        # read back through a sourceEntity='routed' iterate -> proves the write landed under 'routed'
        assert len(engine.capture_result()["back"]) == 3
    finally:
        _clean()


@pytest.mark.parametrize("fmt,ext", [("csv", "csv"), ("json", "json"), ("xlsx", "xlsx")])
def test_target_entity_file_exporter(fmt, ext):
    _clean()
    try:
        _run(f"te_{fmt}.xml")
        routed = list((_DIR / "output").rglob(f"routed*.{ext}"))
        gen = list((_DIR / "output").rglob(f"gen*.{ext}"))
        assert routed, f"targetEntity did not name the {ext} output 'routed' (files: "\
            f"{[p.name for p in (_DIR / 'output').rglob('*.' + ext)]})"
        assert not gen, f"the {ext} output still used the statement name 'gen'"
    finally:
        _clean()


# ---- sourceEntity: READ routes from the physical entity, not the statement name 'reader' ----

def test_source_entity_rdbms():
    _clean()
    try:
        engine = _run("se_rdbms.xml")
        assert sorted(r["n"] for r in engine.capture_result()["reader"]) == [1, 2, 3, 4]
    finally:
        _clean()
