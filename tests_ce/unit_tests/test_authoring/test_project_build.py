# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Build proves a project: the entry descriptor plus its literal include graph (V5 slice b)."""

import shutil
from pathlib import Path, PurePosixPath

import pytest

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId
from datamimic_ce.authoring.domain.proof import VerificationGateStatus
from datamimic_ce.authoring.domain.requests import BuildRequestV4, DecompileDocumentRequest, LintRequest

_PROJECT = Path(__file__).parent / "project_build" / "order_desk"
_ENTRY = PurePosixPath("datamimic.xml")
_ROLES = [
    {"product": "customers", "field": "customer_id", "role": {"kind": "identifier"}},
    {
        "product": "orders",
        "field": "customer_id",
        "role": {"kind": "foreign_key", "parent_product": "customers", "parent_field": "customer_id"},
    },
    {"product": "orders", "field": "order_id", "role": {"kind": "identifier"}},
    {
        "product": "order_rows",
        "field": "order_id",
        "role": {"kind": "foreign_key", "parent_product": "orders", "parent_field": "order_id"},
    },
]


def _build(project: Path = _PROJECT, *, expectations: list[dict] | None = None, roles: list[dict] = _ROLES):
    application = create_authoring_application(project, descriptor_path=_ENTRY)
    decoded = application.decompile_document(
        DecompileDocumentRequest(xml=(project / _ENTRY).read_text(encoding="utf-8"), descriptor_path=_ENTRY)
    )
    assert decoded.outcome == "ready", decoded
    return application.build(
        BuildRequestV4.model_validate(
            {
                "document": decoded.document.model_dump(mode="json"),
                "descriptor_path": str(_ENTRY),
                "product_roles": roles,
                "expectations": expectations or [],
            }
        )
    )


def _copy(tmp_path: Path) -> Path:
    project = tmp_path / "order_desk"
    shutil.copytree(_PROJECT, project)
    return project


def test_project_with_steps_and_memstore_handoff_reaches_ready() -> None:
    result = _build(
        expectations=[
            {"kind": "exact_count", "subject": {"kind": "product", "product": "order_rows"}, "count": 3},
            {
                "kind": "range",
                "subject": {"kind": "product", "product": "order_rows"},
                "field": "total",
                "minimum": "9.5",
                "maximum": "47.5",
            },
        ]
    )
    assert result.outcome == "ready", result.diagnostics
    assert {product.name for product in result.evidence} == {"customers", "orders", "order_rows"}
    # The entry is seeded and its project loads Python, so Build replays it unrequested.
    assert result.verification.deterministic_replay.status is VerificationGateStatus.PASSED


def test_expectation_on_a_step_product_is_checked() -> None:
    result = _build(
        expectations=[{"kind": "exact_count", "subject": {"kind": "product", "product": "orders"}, "count": 4}]
    )
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
    result = _build(project, roles=_ROLES[:3])
    assert result.outcome == "rejected"


@pytest.mark.parametrize(
    ("uri", "inline_setup"),
    [("../outside.xml", False), ("{step}", False), ("model/10_customers.xml", True), ("conf/base.yaml", False)],
)
def test_build_refuses_a_non_literal_or_uncontained_include(tmp_path: Path, uri: str, inline_setup: bool) -> None:
    project = _copy(tmp_path)
    (tmp_path / "outside.xml").write_text("<setup/>", encoding="utf-8")
    (project / "conf" / "base.yaml").write_text("x: 1", encoding="utf-8")
    application = create_authoring_application(project, descriptor_path=_ENTRY)
    decoded = application.decompile_document(
        DecompileDocumentRequest(xml=(project / _ENTRY).read_text(encoding="utf-8"), descriptor_path=_ENTRY)
    )
    document = decoded.document.model_dump(mode="json")
    step = next(
        node for node in document["root"]["children"] if node["properties"].get("uri") == "model/10_customers.xml"
    )
    step["properties"]["uri"] = uri
    if inline_setup:
        step["children"] = [{"kind": "setup", "properties": {}, "children": []}]
    result = application.build(
        BuildRequestV4.model_validate({"document": document, "descriptor_path": str(_ENTRY), "product_roles": _ROLES})
    )
    assert result.outcome == "rejected"
    assert any(item.code in {AuthoringRuleId.INCLUDE, "DM405"} for item in result.diagnostics), result.diagnostics


def test_delivery_rule_spans_the_project(tmp_path: Path) -> None:
    # A file export in delivery/ makes every product of every step need a target (DM407).
    project = _copy(tmp_path)
    step = project / "model" / "20_orders.xml"
    step.write_text(
        step.read_text(encoding="utf-8").replace('target="store" targetEntity="orders"', ""), encoding="utf-8"
    )
    result = _build(project, roles=_ROLES[:2])
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
    result = create_authoring_application(project, descriptor_path=_ENTRY).lint(LintRequest(xml=entry))
    assert any(item.code == "DM401" for item in result.diagnostics), result.diagnostics
