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


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
def test_include_during_unique_draws_copies_only_root_state(tmp_path: Path, wrapped: bool) -> None:
    (tmp_path / "included.xml").write_text(
        '<setup numProcess="1"><generate name="included" count="1" target="">'
        '<key name="copied_code" script="code"/></generate></setup>',
        encoding="utf-8",
    )
    body = '<generate name="rows" count="4" pageSize="2" target="">'
    body += _conditional('<key name="code" type="int" values="1,2,3,4" unique="true"/>', wrapped)
    body += '<include uri="included.xml"/></generate>'
    result = _run(tmp_path, body)
    codes = [row["code"] for row in result["rows"]]
    assert sorted(codes) == [1, 2, 3, 4]
    assert [row["copied_code"] for row in result["included"]] == codes


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
@pytest.mark.parametrize("kind", ["key", "reference"])
def test_unique_cursor_is_scoped_to_each_nested_generate_invocation(
    tmp_path: Path, reference_setup: str, wrapped: bool, kind: str
) -> None:
    field = '<key name="fk" type="int" values="1,2,3,4" unique="true"/>' if kind == "key" else _reference()
    body = reference_setup + '<generate name="parents" count="2" target="">'
    body += '<key name="id" generator="IncrementGenerator"/>'
    body += '<generate name="children" count="4" pageSize="2" target="">'
    body += '<key name="parent_id" script="parent.id"/>' + _conditional(field, wrapped)
    body += "</generate></generate>"
    rows = _run(tmp_path, body)["children"]
    assert len(rows) == 8
    for parent in (1, 2):
        assert sorted(row["fk"] for row in rows if row["parent_id"] == parent) == [1, 2, 3, 4]


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
@pytest.mark.parametrize("scripted", [False, True], ids=["generated-list", "scripted-list"])
def test_unique_cursor_is_scoped_to_each_nested_list_invocation(
    tmp_path: Path, reference_setup: str, wrapped: bool, scripted: bool
) -> None:
    field = '<key name="fk" type="int" values="1,2,3,4" unique="true"/>'
    body = reference_setup + '<generate name="parents" count="2" target="">'
    source = 'script="[{}, {}, {}, {}]"' if scripted else 'type="list"'
    body += f'<nestedKey name="children" count="4" {source}>' + _conditional(field, wrapped)
    body += "</nestedKey></generate>"
    rows = _run(tmp_path, body)["parents"]
    assert len(rows) == 2
    for row in rows:
        assert sorted(child["fk"] for child in row["children"]) == [1, 2, 3, 4]


def test_setup_unique_variable_remains_available_to_later_generates(tmp_path: Path) -> None:
    body = '<variable name="chosen" values="\'A\'" unique="true"/>'
    body += '<generate name="first" count="1" target=""><key name="value" script="chosen"/></generate>'
    body += '<generate name="later" count="2" numProcess="2" target="">'
    body += '<key name="value" script="chosen"/></generate>'
    result = _run(tmp_path, body, seed=False)
    assert result == {"first": [{"value": "A"}], "later": [{"value": "A"}, {"value": "A"}]}


@pytest.mark.parametrize("wrapped", [False, True], ids=["direct", "conditional"])
@pytest.mark.parametrize("nested_list", [False, True], ids=["generate", "nested-list"])
def test_nested_unique_pool_still_fails_when_one_invocation_overdraws(
    tmp_path: Path, wrapped: bool, nested_list: bool
) -> None:
    body = '<generate name="parents" count="2" target="">'
    body += (
        '<nestedKey name="children" type="list" count="3">'
        if nested_list
        else '<generate name="children" count="3" pageSize="1" target="">'
    )
    body += _conditional('<key name="code" type="int" values="1,2" unique="true"/>', wrapped)
    body += '</nestedKey>' if nested_list else '</generate>'
    body += '</generate>'
    with pytest.raises(ValueError, match="unique"):
        _run(tmp_path, body)
