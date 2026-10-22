# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""The include graph's byte budget holds before the parser decodes a literal .properties include (#367)."""

from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters import dryrun
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, LintRequest
from datamimic_ce.engine.dsl.parsers.base import dispatch

_ENTRY = (
    '<setup rngSeed="1"><include uri="conf/base.properties"/>'
    '<generate name="rows" count="1"><key name="x" constant="1"/></generate></setup>'
)


def _project(root: Path) -> Path:
    (root / "conf").mkdir()
    (root / "conf" / "base.properties").write_text("key=" + "v" * 200 + "\n", encoding="utf-8")
    (root / PROJECT_ENTRY_PATH).write_text(_ENTRY, encoding="utf-8")
    return root


def test_lint_refuses_an_oversized_graph_before_the_parser_reads_a_properties_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _project(tmp_path)
    monkeypatch.setattr(dryrun, "_MAX_INCLUDE_GRAPH_BYTES", 64)

    def parser_read(path: Path) -> dict[str, str]:
        raise AssertionError("the parser decoded a properties file before the budget was checked")

    monkeypatch.setattr(dispatch, "parse_properties", parser_read)
    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).lint(LintRequest(xml=_ENTRY))
    assert not result.ok
    assert [item.message for item in result.diagnostics] == [
        "XML include dependency graph exceeds the aggregate byte budget"
    ]


def test_a_graph_within_the_budget_still_lints(tmp_path: Path) -> None:
    root = _project(tmp_path)
    result = create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).lint(LintRequest(xml=_ENTRY))
    assert result.ok, result.diagnostics
