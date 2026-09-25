from __future__ import annotations

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


def test_shape_accepts_nullability_change_when_field_remains() -> None:
    before = {"type": "object", "fields": {"id": "int", "nickname": "null"}}
    after = {"type": "object", "fields": {"id": "int", "nickname": "str"}}

    assert shape_compatible(before, after)


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
