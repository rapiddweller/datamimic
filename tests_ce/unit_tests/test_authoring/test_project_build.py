# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build proves a project: datamimic.xml and its literal include graph against acceptance/build.json (V5)."""

import json
import shutil
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, LintRequest

_PROJECT = Path(__file__).parent / "project_build" / "order_desk"


def _build(project: Path = _PROJECT):
    return create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).build()


def _accept(project: Path, **fields: object) -> None:
    """Replace fields of the copied project's acceptance/build.json."""
    path = project / "acceptance" / "build.json"
    path.write_text(json.dumps({**json.loads(path.read_text(encoding="utf-8")), **fields}), encoding="utf-8")


def _roles(project: Path, count: int) -> None:
    roles = json.loads((_PROJECT / "acceptance" / "build.json").read_text(encoding="utf-8"))["product_roles"]
    _accept(project, product_roles=roles[:count], expectations=[])


def _copy(tmp_path: Path) -> Path:
    project = tmp_path / "order_desk"
    shutil.copytree(_PROJECT, project)
    return project


def test_project_with_steps_and_memstore_handoff_reaches_ready() -> None:
    result = _build()
    assert result.outcome == "ready", result.diagnostics
    assert {product.name for product in result.evidence} == {"customers", "orders", "order_rows"}
    # The entry is seeded and its project loads Python, so Build replays it unrequested.
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


def test_expectation_on_a_step_product_is_checked(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    _accept(
        project, expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "orders"}, "count": 4}]
    )
    result = _build(project)
    assert result.outcome == "rejected"
    assert any(item.path == ("expectations", 0) for item in result.diagnostics), result.diagnostics


def test_library_loaded_by_a_step_forces_replay(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    entry = (project / "datamimic.xml").read_text(encoding="utf-8")
    (project / "datamimic.xml").write_text(
        entry.replace('    <execute uri="lib/pricing.scr.py"/>\n', ""), encoding="utf-8"
    )
    step = (project / "model" / "20_orders.xml").read_text(encoding="utf-8")
    (project / "model" / "20_orders.xml").write_text(
        step.replace("<setup>", '<setup>\n    <execute uri="lib/pricing.scr.py"/>'), encoding="utf-8"
    )
    result = _build(project)
    assert result.outcome == "ready", result.diagnostics
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


def test_client_declared_in_a_step_is_refused(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    step = project / "model" / "10_customers.xml"
    step.write_text(
        step.read_text(encoding="utf-8").replace(
            "<setup>", '<setup>\n    <database id="db" dbms="sqlite" database="x"/>'
        ),
        encoding="utf-8",
    )
    # A nested use of that client must not surface first as an undeclared id.
    nested = project / "delivery" / "90_export.xml"
    nested.write_text(nested.read_text(encoding="utf-8").replace('target="CSV"', 'target="db"'), encoding="utf-8")
    result = _build(project)
    assert result.outcome == "rejected"
    assert [(item.code, item.path[:2]) for item in result.diagnostics] == [
        (AuthoringRuleId.INCLUDE, ("include", "model/10_customers.xml"))
    ], result.diagnostics


def test_product_names_stay_unique_across_files(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    step = project / "delivery" / "90_export.xml"
    step.write_text(step.read_text(encoding="utf-8").replace('name="order_rows"', 'name="orders"'), encoding="utf-8")
    _roles(project, 3)
    result = _build(project)
    assert result.outcome == "rejected"


@pytest.mark.parametrize(
    ("uri", "inline_setup"),
    [("../outside.xml", False), ("{step}", False), ("model/10_customers.xml", True), ("conf/base.yaml", False)],
)
def test_build_refuses_a_non_literal_or_uncontained_include(tmp_path: Path, uri: str, inline_setup: bool) -> None:
    project = _copy(tmp_path)
    (tmp_path / "outside.xml").write_text("<setup/>", encoding="utf-8")
    (project / "conf" / "base.yaml").write_text("x: 1", encoding="utf-8")
    include = f'<include uri="{uri}"><setup/></include>' if inline_setup else f'<include uri="{uri}"/>'
    entry = project / "datamimic.xml"
    entry.write_text(
        entry.read_text(encoding="utf-8").replace('<include uri="model/10_customers.xml"/>', include), encoding="utf-8"
    )
    result = _build(project)
    assert result.outcome == "rejected"
    assert any(item.code in {AuthoringRuleId.INCLUDE, "DM405"} for item in result.diagnostics), result.diagnostics


def test_delivery_rule_spans_the_project(tmp_path: Path) -> None:
    # A file export in delivery/ makes every product of every step need a target (DM407).
    project = _copy(tmp_path)
    step = project / "model" / "20_orders.xml"
    step.write_text(
        step.read_text(encoding="utf-8").replace('target="store" targetEntity="orders"', ""), encoding="utf-8"
    )
    _roles(project, 2)
    result = _build(project)
    assert result.outcome == "rejected"
    assert any(
        item.code == "DM407" and item.path[:2] == ("include", "model/20_orders.xml") for item in result.diagnostics
    ), result.diagnostics


def test_include_graph_bytes_are_bounded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from datamimic_ce.authoring.adapters import dryrun

    monkeypatch.setattr(dryrun, "_MAX_INCLUDE_GRAPH_BYTES", 64)
    result = _build(_copy(tmp_path))
    assert result.outcome == "rejected"
    assert any(item.code is AuthoringRuleId.INCLUDE for item in result.diagnostics), result.diagnostics


def test_step_is_linted_in_the_entry_context_and_findings_name_the_step(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    step = project / "model" / "20_orders.xml"
    # The entry's memstore is known to the step; an undeclared target is still found, at the step's line.
    step.write_text(
        step.read_text(encoding="utf-8").replace('target="store" targetEntity', 'target="nostore" targetEntity'),
        encoding="utf-8",
    )
    result = _build(project)
    assert result.outcome == "rejected"
    step_findings = [item for item in result.diagnostics if item.path[0] == "include"]
    assert [(item.code, item.path) for item in step_findings] == [
        ("DM401", ("include", "model/20_orders.xml", "/setup/generate", "line", 2))
    ], result.diagnostics


def test_runtime_failure_in_a_step_names_the_step(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    step = project / "model" / "20_orders.xml"
    step.write_text(step.read_text(encoding="utf-8").replace("float(unit_price)", "missing_name"), encoding="utf-8")
    result = _build(project)
    assert result.outcome == "rejected"
    assert any(item.path == ("include", "model/20_orders.xml", "key", "script") for item in result.diagnostics), (
        result.diagnostics
    )


def test_memstore_declared_in_a_step_is_known_to_later_steps(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    entry = project / "datamimic.xml"
    entry.write_text(entry.read_text(encoding="utf-8").replace('    <memstore id="store"/>\n', ""), encoding="utf-8")
    step = project / "model" / "10_customers.xml"
    step.write_text(
        step.read_text(encoding="utf-8").replace("<setup>", '<setup>\n    <memstore id="store"/>'), encoding="utf-8"
    )
    result = _build(project)
    assert result.outcome == "ready", result.diagnostics


def test_entry_reads_a_memstore_a_step_declares(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    entry = project / "datamimic.xml"
    delivery = (project / "delivery" / "90_export.xml").read_text(encoding="utf-8")
    inline = delivery.replace("<setup>\n", "").replace("</setup>\n", "")
    entry.write_text(
        entry.read_text(encoding="utf-8")
        .replace('    <memstore id="store"/>\n', "")
        .replace('    <include uri="delivery/90_export.xml"/>\n', inline),
        encoding="utf-8",
    )
    step = project / "model" / "10_customers.xml"
    step.write_text(
        step.read_text(encoding="utf-8").replace("<setup>", '<setup>\n    <memstore id="store"/>'), encoding="utf-8"
    )
    result = _build(project)
    assert result.outcome == "ready", result.diagnostics


def test_an_unseeded_project_reports_the_missing_seed_once(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    entry = project / "datamimic.xml"
    entry.write_text(entry.read_text(encoding="utf-8").replace(' rngSeed="7"', ""), encoding="utf-8")
    result = _build(project)
    assert [item.path[:2] for item in result.diagnostics if item.code == "DM303"] == [("descriptor", "datamimic.xml")]


def test_an_unreadable_graph_is_reported_instead_of_undeclared_ids(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    entry = project / "datamimic.xml"
    delivery = (project / "delivery" / "90_export.xml").read_text(encoding="utf-8")
    inline = delivery.replace("<setup>\n", "").replace("</setup>\n", "")
    entry.write_text(
        entry.read_text(encoding="utf-8")
        .replace('    <memstore id="store"/>\n', "")
        .replace('    <include uri="delivery/90_export.xml"/>\n', inline),
        encoding="utf-8",
    )
    step = project / "model" / "10_customers.xml"
    step.write_text(
        step.read_text(encoding="utf-8").replace("<setup>", '<setup>\n    <memstore id="store"/>'), encoding="utf-8"
    )
    (project / "model" / "20_orders.xml").write_text("<setup>", encoding="utf-8")
    result = _build(project)
    assert result.outcome == "rejected"
    errors = [item.code for item in result.diagnostics if item.severity == "error"]
    assert errors == [AuthoringRuleId.INCLUDE], result.diagnostics


def test_lint_does_not_let_the_entry_see_a_client_a_step_declares(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    step = project / "model" / "10_customers.xml"
    step.write_text(
        step.read_text(encoding="utf-8").replace("<setup>", '<setup>\n    <database id="db"/>'), encoding="utf-8"
    )
    entry = (project / "datamimic.xml").read_text(encoding="utf-8")
    entry = entry.replace("</setup>", '    <generate name="probe" count="1" target="db"/>\n</setup>')
    result = create_authoring_application(project, descriptor_path=PROJECT_ENTRY_PATH).lint(LintRequest(xml=entry))
    assert any(item.code == "DM401" for item in result.diagnostics), result.diagnostics


def test_ready_binds_every_file_the_run_read_and_nothing_else() -> None:
    result = _build()
    assert result.outcome == "ready", result.diagnostics
    assert [item.path.as_posix() for item in result.artifact.files] == [
        "acceptance/build.json",
        "conf/base.properties",
        "data/entity/customers.ent.csv",
        "data/weighting/channel.wgt.csv",
        "datamimic.xml",
        "delivery/90_export.xml",
        "lib/pricing.scr.py",
        "model/10_customers.xml",
        "model/20_orders.xml",
    ]


def test_a_changed_data_file_changes_its_digest_only(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    before = {item.path: item.sha256 for item in _build(project).artifact.files}
    data = project / "data" / "entity" / "customers.ent.csv"
    data.write_text(data.read_text(encoding="utf-8").replace("Ada", "Adele"), encoding="utf-8")
    (project / "README.md").write_text("evidence written after Build", encoding="utf-8")
    after = {item.path: item.sha256 for item in _build(project).artifact.files}
    assert {path for path in before if before[path] != after[path]} == {PurePosixPath("data/entity/customers.ent.csv")}


def test_a_project_without_acceptance_is_rejected(tmp_path: Path) -> None:
    project = _copy(tmp_path)
    (project / "acceptance" / "build.json").unlink()
    result = _build(project)
    assert result.outcome == "rejected"
    assert result.diagnostics[0].code is AuthoringRuleId.INPUT


def test_a_connection_profile_read_during_the_run_is_recorded(tmp_path: Path) -> None:
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
    from datamimic_ce.engine.dsl.api import resource_reader_scope

    (tmp_path / "conf").mkdir()
    (tmp_path / "conf" / "test.env.properties").write_text("db.host=localhost\n", encoding="utf-8")
    workspace = AuthoringWorkspaceContext(tmp_path, PROJECT_ENTRY_PATH)
    read: list[Path] = []

    def recording(path: Path) -> bytes:
        read.append(path)
        return workspace.read_resource_bytes(path)

    with resource_reader_scope(recording):
        assert workspace.load_connection_profile(tmp_path, "test") == {"db.host": "localhost"}
    assert read == [tmp_path / "conf" / "test.env.properties"]


def test_the_default_factory_builds_the_project() -> None:
    # Build proves datamimic.xml whatever descriptor the application's other operations are bound to.
    assert create_authoring_application(_PROJECT).build().outcome == "ready"
