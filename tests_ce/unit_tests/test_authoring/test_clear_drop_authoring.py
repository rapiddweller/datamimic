# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Authoring and clear/drop (BC-4.0-016): lint knows them, bounded execution never runs them and says so, Build keeps
them out of the products it proves. Runtime behavior is pinned by integration_tests/test_clear_drop_operations."""

import sqlite3
from pathlib import Path

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.catalog import CeDslCatalog
from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain, CapabilityFound
from datamimic_ce.authoring.domain.diagnostics import AuthoringSystemDiagnosticCode
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, LintRequest, RunRequest
from tests_ce.authoring_project import build_project

_DB = '<database id="db" dbms="sqlite" database="d"/>'
_CLEAR = '<generate name="clear_items" targetEntity="items" target="db.clear"/>'
_MONGO = '<mongodb id="mongo" host="localhost" port="27017" database="d"/>'
_ROWS = '<generate name="rows" count="2"><key name="x" constant="1"/></generate>'
_READ_AFTER = (
    '<generate name="items_left" source="db" selector="SELECT id FROM items" count="5" distribution="ordered" '
    'target=""/>'
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    (tmp_path / "db").mkdir()
    with sqlite3.connect(tmp_path / "db" / "d.sqlite") as connection:
        connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY)")
        connection.executemany("INSERT INTO items VALUES (?)", [(1,), (2,)])
    return tmp_path


def _rows(workspace: Path) -> int:
    with sqlite3.connect(workspace / "db" / "d.sqlite") as connection:
        return connection.execute("SELECT COUNT(*) FROM items").fetchone()[0]


def _app(workspace: Path):
    return create_authoring_application(workspace, descriptor_path=PROJECT_ENTRY_PATH)


def _request(**fields) -> RunRequest:
    return RunRequest(descriptor_path=PROJECT_ENTRY_PATH, **fields)


def _setup(*children: str, seed: str = ' rngSeed="1"') -> str:
    return f"<setup{seed}>{_DB}{''.join(children)}</setup>"


def _codes(result) -> list[tuple[str, str]]:
    return [(str(item.code), item.severity) for item in result.diagnostics]


def test_lint_accepts_a_count_free_clear_and_drop(workspace: Path):
    mongo = f'{_MONGO}<generate name="drop_docs" targetEntity="docs" target="mongo.drop"/>'
    result = _app(workspace).lint(LintRequest(xml=f'<setup rngSeed="1">{_DB}{_CLEAR}{mongo}</setup>'))
    assert result.ok, result.diagnostics


def test_lint_knows_the_operations_of_each_client_family(workspace: Path):
    rdbms_drop = _setup('<generate name="drop_items" targetEntity="items" target="db.drop"/>')
    result = _app(workspace).lint(LintRequest(xml=rdbms_drop))
    assert [item.code for item in result.diagnostics if item.severity == "error"] == ["DM401"]
    mongo = f'<setup rngSeed="1">{_MONGO}<generate name="c" targetEntity="d" target="mongo.drop"/></setup>'
    assert _app(workspace).lint(LintRequest(xml=mongo)).ok


def test_dry_run_skips_the_clear_reports_it_and_leaves_the_rows(workspace: Path):
    result = _app(workspace).dry_run(_request(xml=_setup(_CLEAR, _READ_AFTER)))
    assert result.ok
    assert [(product.name, len(product.rows)) for product in result.products] == [("items_left", 2)]
    (warning,) = result.diagnostics
    assert (warning.code, warning.severity) == (AuthoringSystemDiagnosticCode.NOT_EXECUTED, "warning")
    assert "clear_items" in warning.message
    assert _rows(workspace) == 2


@pytest.mark.parametrize(
    ("statement", "reason"),
    [
        ('<generate name="c" targetEntity="items" count="1" target="db.clear"/>', "forbidden attributes: count"),
        ('<generate name="c" count="1" target="db.clear"/>', "clear and drop require explicit targetEntity"),
        (
            '<generate name="outer" count="1"><generate name="c" targetEntity="items" target="db.clear"/></generate>',
            "root-only operations",
        ),
    ],
)
def test_a_clear_with_a_wrong_shape_is_refused_with_i928_in_every_mode(workspace: Path, statement: str, reason: str):
    for run in (_app(workspace).dry_run, _app(workspace).run):
        result = run(_request(xml=_setup(statement), allow_side_effects=run == _app(workspace).run))
        assert not result.ok
        (error,) = (item for item in result.diagnostics if item.severity == "error")
        assert error.ce_error is not None and error.ce_error.issue_code == "I928"
    assert _rows(workspace) == 2


def test_a_descriptor_that_only_clears_is_a_successful_dry_run_with_the_warning(workspace: Path):
    result = _app(workspace).dry_run(_request(xml=_setup(_CLEAR)))
    assert result.ok
    assert result.products == ()
    assert [str(item.code) for item in result.diagnostics] == ["not_executed"]
    assert _rows(workspace) == 2


def test_run_with_side_effects_clears_inside_the_contained_run_only(workspace: Path):
    result = _app(workspace).run(_request(xml=_setup(_CLEAR, _READ_AFTER), allow_side_effects=True))
    assert [(product.name, len(product.rows)) for product in result.products] == [("items_left", 0)]
    assert AuthoringSystemDiagnosticCode.NOT_EXECUTED.value not in [
        str(item.code) for item in result.diagnostics if "destructive" in item.message
    ]
    assert _rows(workspace) == 2  # the workspace database is a private copy in a contained run


def test_build_proves_the_products_and_reports_the_clear_it_did_not_run(workspace: Path):
    result = build_project(
        workspace,
        _setup(_CLEAR, _ROWS),
        version="5.0",
        environment_bindings=[{"environment": "db", "family": "database"}],
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 2}],
    )
    assert result.outcome == "ready", result.diagnostics
    assert [product.name for product in result.evidence] == ["rows"]
    assert result.assurance.mode == "target_isolated"
    (warning,) = [item for item in result.diagnostics if item.severity == "warning"]
    assert "clear_items" in warning.message
    assert _rows(workspace) == 2


def test_build_of_a_project_that_only_cleans_up_has_no_product_to_prove_and_is_rejected(workspace: Path):
    result = build_project(
        workspace,
        _setup(_CLEAR),
        version="5.0",
        environment_bindings=[{"environment": "db", "family": "database"}],
    )
    assert result.outcome == "rejected"
    assert _rows(workspace) == 2


def test_a_skipped_clear_does_not_turn_a_zero_row_build_into_ready(workspace: Path):
    zero = '<generate name="rows" count="0"><key name="x" constant="1"/></generate>'
    expectations = [{"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 0}]
    bindings = [{"environment": "db", "family": "database"}]
    alone = build_project(
        workspace, _setup(zero), version="5.0", environment_bindings=bindings, expectations=expectations
    )
    with_clear = build_project(
        workspace, _setup(_CLEAR, zero), version="5.0", environment_bindings=bindings, expectations=expectations
    )
    assert alone.outcome == with_clear.outcome == "rejected"


def test_build_rejects_a_clear_that_would_not_run_as_written(workspace: Path):
    result = build_project(
        workspace,
        _setup('<generate name="clear_items" targetEntity="items" count="1" target="db.clear"/>', _ROWS),
        version="5.0",
        environment_bindings=[{"environment": "db", "family": "database"}],
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "rows"}, "count": 2}],
    )
    assert result.outcome == "rejected"
    assert any(item.ce_error is not None and item.ce_error.issue_code == "I928" for item in result.diagnostics)
    assert _rows(workspace) == 2


def test_the_capability_catalog_lists_the_operations_per_client_family():
    snapshot = CeDslCatalog(CeDmJsonCodec()).snapshot()
    families = {}
    for name in ("database", "mongodb"):
        found = snapshot.capability(CapabilityDomain.TARGET_FAMILY, name)
        assert isinstance(found, CapabilityFound)
        families[name] = found.capability.operations
    assert families["database"] == ("insert", "update", "upsert", "delete", "clear")
    assert families["mongodb"] == ("insert", "update", "upsert", "delete", "clear", "drop")
