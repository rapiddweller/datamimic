# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import sqlite3
from pathlib import Path

import pytest

from datamimic_ce.authoring.adapters.linter import lint_source
from datamimic_ce.engine.dsl.api import (
    EXPORTER_CONSOLE_EXPORTER,
    EXPORTER_LOG_EXPORTER,
    EXPORTER_TEST_RESULT_EXPORTER,
)
from datamimic_ce.engine.dsl.vocabulary.constants.exporter_constants import BUILTIN_TARGET_NAMES
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


@pytest.mark.parametrize("client", sorted(BUILTIN_TARGET_NAMES))
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


def test_the_reserved_ids_are_exactly_the_exporters_a_bare_target_resolves() -> None:
    """The one owner lists every built-in exporter; a new exporter without an entry fails here."""
    diagnostic_exporters = {EXPORTER_CONSOLE_EXPORTER, EXPORTER_LOG_EXPORTER, EXPORTER_TEST_RESULT_EXPORTER}
    assert buffered_exporter_names() | diagnostic_exporters == BUILTIN_TARGET_NAMES


@pytest.mark.parametrize("client", sorted(BUILTIN_TARGET_NAMES))
def test_lint_refuses_every_reserved_id(client: str) -> None:
    xml = f'<setup rngSeed="1"><database id="{client}" dbms="sqlite" database="a"/></setup>'
    assert any(d.rule == "DM409" for d in lint_source(xml).diagnostics)
