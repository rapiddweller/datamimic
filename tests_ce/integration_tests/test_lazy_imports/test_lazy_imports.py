# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_FIXTURES = Path(__file__).parent
_ROOT = _FIXTURES.parents[2]
_LIBRARIES = {"numpy", "pandas", "pyarrow", "sqlalchemy", "pymongo", "bson", "oracledb", "mysql", "requests"}
_RUN_AND_REPORT_IMPORTS = """
import sys
import json
from datamimic_ce.interfaces.cli.__main__ import main

try:
    main()
except SystemExit as result:
    if result.code:
        raise
print("IMPORTS", json.dumps(sorted(sys.modules)))
"""


def _run(descriptor: str, directory: Path) -> tuple[set[str], Path]:
    directory.mkdir()
    shutil.copyfile(_FIXTURES / descriptor, directory / descriptor)
    result = subprocess.run(
        [sys.executable, "-c", _RUN_AND_REPORT_IMPORTS, "run", descriptor, "--task-id", "lazy-imports"],
        cwd=directory,
        env={**os.environ, "PYTHONPATH": str(_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    imports = next(line.removeprefix("IMPORTS ") for line in result.stdout.splitlines() if line.startswith("IMPORTS "))
    (output,) = directory.rglob("rows.csv")
    return set(json.loads(imports)), output


def test_csv_run_does_not_import_unused_dependencies(tmp_path):
    modules, output = _run("csv.xml", tmp_path / "csv")

    assert modules & _LIBRARIES == set()
    assert output.read_text().splitlines() == ["value", "1", "2", "3"]


def test_sqlite_run_imports_sqlalchemy_only(tmp_path):
    modules, output = _run("sqlite.xml", tmp_path / "sqlite")

    assert modules & _LIBRARIES == {"sqlalchemy"}
    assert output.read_text().splitlines() == ["value", "1"]


def test_numpy_expression_imports_numpy_only(tmp_path):
    modules, output = _run("numpy.xml", tmp_path / "numpy")

    assert modules & _LIBRARIES == {"numpy"}
    assert output.read_text().splitlines() == ["value", "9"]


def test_seeded_pandas_and_numpy_expressions_replay(tmp_path):
    modules, first = _run("seeded.xml", tmp_path / "first")
    _, second = _run("seeded.xml", tmp_path / "second")

    assert {"numpy", "pandas"} <= modules
    assert modules & (_LIBRARIES - {"numpy", "pandas", "pyarrow"}) == set()
    assert first.read_bytes() == second.read_bytes()
    with first.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 3
    assert all(int(row["value"]) == int(row["draw"]) + 5 and row["year"] == "2020" for row in rows)
