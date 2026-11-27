"""Consistency matrix for sourceEntity / targetEntity across every source and target.

Proves the read/write-entity resolution is applied at the right (single) abstraction point:
- targetEntity routes the WRITE to its physical entity for every target family (store + file).
- sourceEntity routes the READ from its physical entity for every multi-entity source.
The statement name ('gen'/'reader') always differs from the routed entity ('routed'/'seeded'),
so a pass can only mean the entity attribute took effect.
"""

from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest
from datamimic_ce.engine.io.clients.rdbms_client import RdbmsClient
from datamimic_ce.engine.io.connection_config.rdbms_connection_config import RdbmsConnectionConfig


def _table_rows(database: str, table: str) -> int:
    cfg = RdbmsConnectionConfig(
        dbms="sqlite", database=database, host=None, port=None, user=None, password=None, db_schema=None
    )
    return RdbmsClient(cfg, task_id="t").get(f"SELECT COUNT(*) FROM {table}")[0][0]


def _run(project_dir: Path, filename: str) -> DataMimicTest:
    engine = DataMimicTest(test_dir=project_dir, filename=filename, capture_test_result=True)
    engine.test_with_timer()
    return engine


# ---- targetEntity: WRITE routes to the physical entity, not the statement name 'gen' ----


def test_target_entity_rdbms(project_dir):
    _run(project_dir, "te_rdbms.xml")
    assert _table_rows("matrix_rdbms", "routed") == 3


def test_target_entity_memstore(project_dir):
    engine = _run(project_dir, "te_memstore.xml")
    # read back through a sourceEntity='routed' iterate -> proves the write landed under 'routed'
    assert len(engine.capture_result()["back"]) == 3


@pytest.mark.parametrize("fmt,ext", [("csv", "csv"), ("json", "json"), ("xlsx", "xlsx")])
def test_target_entity_file_exporter(project_dir, fmt, ext):
    _run(project_dir, f"te_{fmt}.xml")
    output = project_dir / "output"
    routed = list(output.rglob(f"routed*.{ext}"))
    gen = list(output.rglob(f"gen*.{ext}"))
    assert routed, (
        f"targetEntity did not name the {ext} output 'routed' (files: {[p.name for p in output.rglob('*.' + ext)]})"
    )
    assert not gen, f"the {ext} output still used the statement name 'gen'"


# ---- targetEntity for RDBMS write OPERATIONS (update/delete), statement name 'gen' != table ----


def test_target_entity_rdbms_update(project_dir):
    _run(project_dir, "te_rdbms_update.xml")
    cfg = RdbmsConnectionConfig(
        dbms="sqlite", database="matrix_upd", host=None, port=None, user=None, password=None, db_schema=None
    )
    rows = RdbmsClient(cfg, task_id="t").get("SELECT tier FROM customers")
    assert [r[0] for r in rows] == ["gold", "gold"]  # targetEntity routed the UPDATE


def test_target_entity_rdbms_delete(project_dir):
    _run(project_dir, "te_rdbms_delete.xml")
    assert _table_rows("matrix_del", "customers") == 0  # targetEntity routed the DELETE


# ---- sourceEntity: READ routes from the physical entity, not the statement name ----


def test_source_entity_rdbms(project_dir):
    engine = _run(project_dir, "se_rdbms.xml")
    assert sorted(r["n"] for r in engine.capture_result()["reader"]) == [1, 2, 3, 4]


def test_source_entity_variable_rdbms(project_dir):
    engine = _run(project_dir, "se_variable.xml")
    # the <variable sourceEntity='people'> must read the seeded table, not statement name 'p'
    assert sorted(r["n"] for r in engine.capture_result()["out"]) == [5, 6, 7]


def test_source_entity_on_single_entity_file_is_ignored_not_fatal(project_dir):
    engine = _run(project_dir, "se_file_ignored.xml")  # sourceEntity on a flat csv must not crash
    assert len(engine.capture_result()["rows"]) == 3


def test_nested_key_file_source_type_is_a_structure_marker(project_dir):
    # A <nestedKey source=file type=list>: source is a file, type='list' is the STRUCTURE marker.
    # Each order gets the 2-item list read from the file.
    rows = _run(project_dir, "nk_source.xml").capture_result()["orders"]
    assert all(len(r["lines"]) == 2 for r in rows)


def test_nested_key_memstore_source_honours_sourceentity(project_dir):
    # nestedKey is NOT file-only: it also reads a memstore. sourceEntity='lineitems' names the memstore
    # entity while type='list' stays the structure marker - the two are cleanly separated, and the
    # memstore read goes through the SAME resolve_source_entity as generate/iterate/variable.
    rows = _run(project_dir, "nk_memstore.xml").capture_result()["orders"]
    assert all(len(r["lines"]) == 2 for r in rows)  # each order got the 2 seeded lineitems


def test_target_entity_rejects_a_path(project_dir):
    # targetEntity is a plain entity name, never a path - a '/' or '..' would escape the output dir.
    with pytest.raises(Exception, match=r"not a path"):
        _run(project_dir, "te_path.xml")


def test_source_entity_variable_memstore(project_dir):
    # covers the variable + memstore read path (variable_task) via sourceEntity
    engine = _run(project_dir, "se_variable_memstore.xml")
    assert len(engine.capture_result()["out"]) == 3
