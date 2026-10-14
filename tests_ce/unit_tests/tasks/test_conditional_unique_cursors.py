"""Finite unique draws survive conditional task rebuilding and page boundaries."""

from __future__ import annotations

import multiprocessing.context
from pathlib import Path

import pytest

from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest


def _conditional(child: str, wrapped: bool) -> str:
    return f'<condition><if condition="True">{child}</if></condition>' if wrapped else child


def _run(directory: Path, body: str, *, seed: bool = True, workers: int = 2) -> dict[str, list[dict]]:
    descriptor = directory / "unique.xml"
    descriptor.write_text(
        f'<setup numProcess="{workers}"' + (' rngSeed="11"' if seed else "") + ">" + body + "</setup>",
        encoding="utf-8",
    )
    engine = DataMimicTest(test_dir=directory, filename=descriptor.name, capture_test_result=True)
    engine.test_with_timer()
    return engine.capture_result()


@pytest.fixture
def reference_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "items.scr.sql").write_text(
        "DROP TABLE IF EXISTS items; CREATE TABLE items (id INTEGER); "
        "INSERT INTO items (id) VALUES (3), (1), (4), (2), (1);",
        encoding="utf-8",
    )
    return (
        '<database id="refdb" database="conditional_unique" dbms="sqlite"/>'
        '<execute uri="items.scr.sql" target="refdb"/>'
    )


def _reference(*, unique: bool = True, name: str = "fk") -> str:
    selection = 'unique="true"' if unique else 'distribution="ordered" cyclic="true"'
    return (
        f'<reference name="{name}" source="refdb" sourceType="items" sourceKey="id" {selection}/>'
    )


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
def test_unique_reference_preserves_distinct_pool_across_pages_and_replays(
    tmp_path: Path, reference_setup: str, wrapped: bool
) -> None:
    body = reference_setup + '<generate name="events" count="4" pageSize="2" target="">'
    body += _conditional(_reference(), wrapped) + "</generate>"
    first = _run(tmp_path, body)
    assert [row["fk"] for row in first["events"]] == [1, 4, 2, 3]
    assert _run(tmp_path, body) == first


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
def test_unique_reference_exhaustion_fails_instead_of_restarting(
    tmp_path: Path, reference_setup: str, wrapped: bool
) -> None:
    body = reference_setup + '<generate name="events" count="5" pageSize="2" target="">'
    body += _conditional(_reference(), wrapped) + "</generate>"
    with pytest.raises(ValueError, match="unique"):
        _run(tmp_path, body)


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
def test_cyclic_reference_keeps_rotation_across_pages(
    tmp_path: Path, reference_setup: str, wrapped: bool
) -> None:
    body = reference_setup + '<generate name="events" count="7" pageSize="2" target="">'
    body += _conditional(_reference(unique=False), wrapped) + "</generate>"
    assert [row["fk"] for row in _run(tmp_path, body)["events"]] == [1, 1, 2, 3, 4, 1, 1]


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
@pytest.mark.parametrize("workers", [1, 2])
def test_inline_unique_values_remain_distinct_with_requested_workers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, wrapped: bool, workers: int
) -> None:
    pools: list[int] = []
    pool = multiprocessing.context.SpawnContext.Pool

    def record_pool(self, processes=None, *args, **kwargs):
        pools.append(processes)
        return pool(self, processes, *args, **kwargs)

    monkeypatch.setattr(multiprocessing.context.SpawnContext, "Pool", record_pool)
    key = '<key name="code" type="int" values="1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16" unique="true"/>'
    body = '<generate name="rows" count="16" pageSize="3" target="" mpPlatform="multiprocessing">'
    body += '<key name="row_id" generator="IncrementGenerator"/>' + _conditional(key, wrapped) + "</generate>"
    rows = _run(tmp_path, body, seed=False, workers=workers)["rows"]
    assert sorted(row["code"] for row in rows) == list(range(1, 17))
    assert [row["row_id"] for row in rows] == list(range(1, 17))
    assert all(type(row["code"]) is int for row in rows)
    assert pools == []  # CE's global uniqueness policy must also cover conditional children.


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
def test_inline_unique_values_exhaustion_is_bounded(tmp_path: Path, wrapped: bool) -> None:
    key = '<key name="code" type="int" values="1,2,2,3,4" unique="true"/>'
    body = '<generate name="rows" count="5" pageSize="2" target="">'
    body += _conditional(key, wrapped) + "</generate>"
    with pytest.raises(ValueError, match="unique"):
        _run(tmp_path, body)


def test_same_named_branch_keys_have_separate_finite_cursors_and_replay(tmp_path: Path) -> None:
    body = '<generate name="rows" count="8" pageSize="3" target="">'
    body += '<key name="id" generator="IncrementGenerator"/><condition>'
    body += '<if condition="id % 2 == 1"><key name="code" type="int" values="1,2,3,4" unique="true"/></if>'
    body += '<else><key name="code" type="int" values="1,2,3,4" unique="true"/></else>'
    body += "</condition></generate>"
    first = _run(tmp_path, body)
    rows = first["rows"]
    assert sorted(row["code"] for row in rows[::2]) == [1, 2, 3, 4]
    assert sorted(row["code"] for row in rows[1::2]) == [1, 2, 3, 4]
    assert _run(tmp_path, body) == first


def test_same_named_branch_references_and_later_statements_have_separate_cursors(
    tmp_path: Path, reference_setup: str
) -> None:
    body = reference_setup + '<generate name="rows" count="8" pageSize="3" target="">'
    body += '<key name="id" generator="IncrementGenerator"/><condition>'
    body += '<if condition="id % 2 == 1">' + _reference() + "</if><else>" + _reference() + "</else>"
    body += '</condition></generate><generate name="later" count="4" pageSize="2" target="">'
    body += _conditional(_reference(), True) + "</generate>"
    first = _run(tmp_path, body)
    assert sorted(row["fk"] for row in first["rows"][::2]) == [1, 2, 3, 4]
    assert sorted(row["fk"] for row in first["rows"][1::2]) == [1, 2, 3, 4]
    assert sorted(row["fk"] for row in first["later"]) == [1, 2, 3, 4]
    assert _run(tmp_path, body) == first


def test_unique_values_do_not_block_later_include_or_multiprocessing(tmp_path: Path) -> None:
    (tmp_path / "included.xml").write_text(
        '<setup numProcess="1"><generate name="included" count="1" target="">'
        '<key name="code" constant="included"/></generate></setup>',
        encoding="utf-8",
    )
    body = '<generate name="first" count="1" target="">'
    body += _conditional('<key name="code" values="1,2,3,4" unique="true"/>', True) + "</generate>"
    body += '<include uri="included.xml"/>'
    body += '<generate name="later" count="4" numProcess="2" target="" mpPlatform="multiprocessing">'
    body += '<key name="id" generator="IncrementGenerator"/></generate>'
    result = _run(tmp_path, body, seed=False)
    assert len(result["first"]) == 1
    assert result["included"] == [{"code": "included"}]
    assert sorted(row["id"] for row in result["later"]) == [1, 2, 3, 4]
