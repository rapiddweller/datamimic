from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from script.architecture_study.compare_step0 import comparable, inventory_by_path, shape_compatible
from script.architecture_study.verify_step0 import CHILD, REPO, RESULT_PREFIX


def test_shape_rejects_missing_object_field() -> None:
    before = {"type": "object", "fields": {"id": "int", "name": "str"}}
    after = {"type": "object", "fields": {"id": "int"}}

    assert not shape_compatible(before, after)


def test_shape_rejects_missing_union_alternative() -> None:
    before = {"type": "union", "values": ["int", "str"]}
    after = {"type": "union", "values": ["int"]}

    assert not shape_compatible(before, after)


def test_shape_rejects_changed_union_member_even_when_both_allow_null() -> None:
    before = {"type": "union", "values": ["int", "null"]}
    after = {"type": "union", "values": ["str", "null"]}

    assert not shape_compatible(before, after)


def test_shape_rejects_unknown_against_concrete_type() -> None:
    assert not shape_compatible("unknown", "int")


def test_shape_does_not_accept_different_field_presence_counts() -> None:
    before = {
        "type": "object",
        "fields": {"name": "str"},
        "presence_counts": {"name": {"present": 1, "total": 2}},
    }
    after = {
        "type": "object",
        "fields": {"name": "str"},
        "presence_counts": {"name": {"present": 2, "total": 2}},
    }

    assert not shape_compatible(before, after)


def test_shape_does_not_accept_legacy_object_without_presence_metadata() -> None:
    legacy_shape = {"type": "object", "fields": {"id": "int"}}

    assert not shape_compatible(legacy_shape, legacy_shape)


def test_shape_does_not_accept_incomplete_presence_metadata() -> None:
    incomplete_shape = {
        "type": "object",
        "fields": {"id": "int", "name": "str"},
        "presence_counts": {"id": {"present": 2, "total": 2}},
    }

    assert not shape_compatible(incomplete_shape, incomplete_shape)


def test_shape_does_not_accept_legacy_object_values_without_presence_metadata() -> None:
    legacy_map_shape = {"type": "object", "values": "int"}

    assert not shape_compatible(legacy_map_shape, legacy_map_shape)


def test_shape_accepts_null_sample_when_field_and_concrete_type_remain() -> None:
    before = {
        "type": "object",
        "fields": {"nickname": {"type": "union", "values": ["int", "null"]}},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }
    after = {
        "type": "object",
        "fields": {"nickname": "int"},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }

    assert shape_compatible(before, after)


def test_shape_does_not_accept_all_null_against_concrete_type() -> None:
    before = {
        "type": "object",
        "fields": {"nickname": "null"},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }
    after = {
        "type": "object",
        "fields": {"nickname": "int"},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }

    assert not shape_compatible(before, after)


def test_shape_does_not_accept_identical_all_null_field_as_structural_proof() -> None:
    all_null_shape = {
        "type": "object",
        "fields": {"nickname": "null"},
        "presence_counts": {"nickname": {"present": 2, "total": 2}},
    }

    assert not shape_compatible(all_null_shape, all_null_shape)


def test_child_records_actual_rows_for_dynamic_count(tmp_path: Path) -> None:
    descriptor = tmp_path / "count_expression.xml"
    shutil.copy2(REPO / "tests_ce/integration_tests/test_count_expression/count_expression.xml", descriptor)
    env = {**os.environ, "PYTHONPATH": str(REPO)}
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(descriptor)],
        cwd=REPO,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    record_line = next(line for line in result.stdout.splitlines() if line.startswith(RESULT_PREFIX))
    record = json.loads(record_line.removeprefix(RESULT_PREFIX))
    assert record["outcome"] == "ok"
    assert record["products"]["orders"]["rows"] == 12
    assert record["products"]["orders"]["value_shape"]["presence_counts"]["i"] == {
        "present": 12,
        "total": 12,
    }


def test_child_capture_and_comparison_reject_nested_field_removal(tmp_path: Path) -> None:
    descriptor = tmp_path / "nested.xml"
    descriptor.write_text(
        '<setup><generate name="orders" count="2" target="">'
        '<key name="order_id" generator="IncrementGenerator"/>'
        '<nestedKey name="items" type="list" count="2">'
        '<key name="line_no" generator="IncrementGenerator"/>'
        '<key name="amount" type="int" min="10" max="20"/>'
        "</nestedKey></generate></setup>",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(descriptor)],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(REPO)},
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    record_line = next(line for line in result.stdout.splitlines() if line.startswith(RESULT_PREFIX))
    record = json.loads(record_line.removeprefix(RESULT_PREFIX))
    shape = record["products"]["orders"]["value_shape"]
    item_shape = shape["fields"]["items"]["items"]
    assert set(item_shape["fields"]) == {"amount", "line_no"}

    changed_shape = copy.deepcopy(shape)
    del changed_shape["fields"]["items"]["items"]["fields"]["line_no"]
    assert not shape_compatible(shape, changed_shape)


def test_child_rejects_import_outside_its_pythonpath_root(tmp_path: Path) -> None:
    descriptor = tmp_path / "safe.xml"
    descriptor.write_text(
        '<setup><generate name="items" count="1" target="">'
        '<key name="id" generator="IncrementGenerator"/>'
        "</generate></setup>",
        encoding="utf-8",
    )
    env = {**os.environ, "PYTHONPATH": str(tmp_path / "empty-pythonpath")}
    (tmp_path / "empty-pythonpath").mkdir()
    result = subprocess.run(
        [sys.executable, "-c", CHILD, str(descriptor)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0 or RESULT_PREFIX not in result.stdout
    assert "PYTHONPATH" in output or "import root" in output.lower()


def test_evidence_line_moves_are_ignored_by_inventory_and_comparable() -> None:
    before_evidence = [
        "tests_ce/test_rows.py:10 tests orders; assertions at tests_ce/test_rows.py:14"
    ]
    after_evidence = [
        "tests_ce/test_rows.py:20 tests orders; assertions at tests_ce/test_rows.py:24"
    ]
    before = {"path": "tests_ce/orders.xml", "category": ["runnable"], "evidence": before_evidence}
    after = {"path": "tests_ce/orders.xml", "category": ["runnable"], "evidence": after_evidence}

    assert inventory_by_path([before]) == inventory_by_path([after])
    assert comparable({**before, "status": "UNVERIFIED"}) == comparable(
        {**after, "status": "UNVERIFIED"}
    )


def test_evidence_normalization_preserves_test_path_and_semantics() -> None:
    evidence = "tests_ce/test_rows.py:10 tests orders; assertions at tests_ce/test_rows.py:14"
    baseline = {"path": "tests_ce/orders.xml", "category": ["runnable"], "evidence": [evidence]}
    changed_path = {**baseline, "evidence": [evidence.replace("test_rows.py", "test_other.py")]}
    changed_semantics = {**baseline, "evidence": [evidence.replace("tests orders", "tests users")]}

    assert inventory_by_path([baseline]) != inventory_by_path([changed_path])
    assert inventory_by_path([baseline]) != inventory_by_path([changed_semantics])
    for changed in (changed_path, changed_semantics):
        assert comparable({**baseline, "status": "UNVERIFIED"}) != comparable(
            {**changed, "status": "UNVERIFIED"}
        )
