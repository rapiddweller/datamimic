# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import sqlite3
from pathlib import Path

import pytest

from datamimic_ce.authoring.adapters.linter import lint_source
from datamimic_ce.authoring.domain.rules.cross_statement import _STATIC_TARGETS
from datamimic_ce.engine.io.api import buffered_exporter_names
from datamimic_ce.interfaces.python.data_mimic_test import DataMimicTest

_GENERATE = (
    '<generate name="items" count="2" target="{target}" createTable="true">'
    '<id name="id" generator="IncrementGenerator"/></generate>'
)


def _run(tmp_path: Path, client: str, target: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)  # the sqlite file is created under ./db
    (tmp_path / "m.xml").write_text(
        f'<setup multiprocessing="0" rngSeed="1"><database id="{client}" dbms="sqlite" database="t"/>'
        + _GENERATE.format(target=target)
        + "</setup>",
        encoding="utf-8",
    )
    DataMimicTest(tmp_path, "m.xml").test_with_timer()


@pytest.mark.parametrize("client", sorted(_STATIC_TARGETS | buffered_exporter_names()))
def test_run_rejects_client_id_equal_to_builtin_exporter(
    tmp_path: Path, client: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#730: the bare target wrote the exporter and createTable made no table, without an error."""
    with pytest.raises(Exception, match="built-in exporter name"):
        _run(tmp_path, client, client, monkeypatch)
    assert not list(tmp_path.rglob("t.sqlite"))


def test_run_creates_the_table_for_a_distinct_client_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _run(tmp_path, "csvdb", "csvdb", monkeypatch)
    with sqlite3.connect(next(tmp_path.rglob("t.sqlite"))) as connection:
        assert connection.execute("select count(*) from items").fetchone() == (2,)


def test_lint_and_run_refuse_the_same_ids() -> None:
    """Lint and the run each compose the reserved ids; every one of them is refused by both."""
    for name in _STATIC_TARGETS | buffered_exporter_names():
        assert any(
            d.rule == "DM409"
            for d in lint_source(
                f'<setup rngSeed="1"><database id="{name}" dbms="sqlite" database="a"/></setup>'
            ).diagnostics
        ), name
    assert lint_source('<setup rngSeed="1"><database id="CSV" dbms="sqlite" database="a"/></setup>').diagnostics
