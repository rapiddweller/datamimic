# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Architecture gate: lint coverage for declared model constraints is GENERIC.

Adding a fact to any registered model's ``__constraints__`` must produce lint
diagnostics with ZERO rules-file changes. Proven the strongest available way: a
synthetic model (never seen by any rule module) is registered once in the central
element registry under a fake tag, and the rules phase fires on its declared facts.

The rules phase (linter._run_rules) is invoked directly on a parsed lxml tree
instead of lint_source, because the phase-2 engine parse would reject the fake
tag — phase 1 is exactly the layer this gate is about. build_schema_index() is
revision-cached, so registration and removal automatically produce fresh views."""

import inspect
from typing import ClassVar

from lxml import etree
from pydantic import BaseModel

from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.linter import _run_rules, lint_source
from datamimic_ce.authoring.schema import build_schema_index
from datamimic_ce.model.constraints import (
    AllOrNone,
    AllowedValuesWhen,
    Constraint,
    Forbids,
    ForbidsWhenValue,
    MutuallyExclusive,
    MutuallyExclusiveWhen,
    RequiredOneOf,
    Requires,
    RequiresWhenValue,
    ValidValues,
)
from datamimic_ce.model.element_registry import (
    ElementDefinition,
    register_element_extension,
    unregister_element_extension,
)

_TAG = "syntheticelement"

_SYNTHETIC_CONSTRAINTS: tuple[Constraint, ...] = (
    RequiredOneOf(frozenset(("alpha", "beta"))),
    MutuallyExclusive(frozenset(("alpha", "beta"))),
    # lint_only fact: the engine executor skips it — checking it is the lint layer's job
    Requires("gamma", frozenset(("source",)), lint_only=True),
    Requires("delta", frozenset(("source",))),
    AllOrNone(frozenset(("windowa", "windowb"))),
    Forbids("alpha", frozenset(("omega",))),
    ValidValues("flavor", ("sweet", "sour")),
    AllowedValuesWhen("mode", ("safe",), "enabled", when_true=True),
    MutuallyExclusiveWhen("source", frozenset(("kind", "selector"))),
    RequiresWhenValue("shape", frozenset(("list",)), frozenset(("count",)), lint_only=True),
    ForbidsWhenValue("shape", frozenset(("literal",)), frozenset(("count",))),
)


class _SyntheticModel(BaseModel):
    """A model no rule module has ever heard of, carrying one fact of every kind."""

    __constraints__: ClassVar[tuple[Constraint, ...]] = _SYNTHETIC_CONSTRAINTS

    name: str | None = None
    alpha: str | None = None
    beta: str | None = None
    gamma: str | None = None
    delta: str | None = None
    source: str | None = None
    windowa: str | None = None
    windowb: str | None = None
    omega: str | None = None
    flavor: str | None = None
    mode: str | None = None
    enabled: bool | None = None
    kind: str | None = None
    selector: str | None = None
    shape: str | None = None
    count: str | None = None


def _lint_synthetic(body_attrs: str) -> list[Diagnostic]:
    """Register structure and rules in their SPOTs, run rules, then restore."""
    register_element_extension(ElementDefinition(_TAG, _SyntheticModel, None), _SYNTHETIC_CONSTRAINTS)
    try:
        root = etree.fromstring(f'<setup rngSeed="1"><{_TAG} name="s" {body_attrs}/></setup>'.encode())
        return [diag for diag in _run_rules(root, base_dir=None) if diag.element == _TAG]
    finally:
        unregister_element_extension(_TAG)


def _rules_fired(body_attrs: str) -> set[str]:
    return {diag.rule for diag in _lint_synthetic(body_attrs)}


def _lint_rules_xml(xml: str) -> list[Diagnostic]:
    return _run_rules(etree.fromstring(xml.encode()), base_dir=None)


def test_required_one_of_fact_lints_generically() -> None:
    assert "DM203" in _rules_fired("")  # neither alpha nor beta -> no value source
    assert "DM203" not in _rules_fired('alpha="1"')


def test_mutually_exclusive_fact_lints_generically() -> None:
    diags = _lint_synthetic('alpha="1" beta="2"')
    mixed = [d for d in diags if d.rule == "DM203"]
    assert mixed, diags
    assert "alpha, beta" in mixed[0].message


def test_lint_only_requires_fact_lints_generically() -> None:
    # gamma => source is lint_only: precisely the lint layer's job (engine skips it)
    diags = [d for d in _lint_synthetic('alpha="1" gamma="x"') if d.rule == "DM214"]
    assert diags and "gamma" in diags[0].message and "source" in diags[0].message
    assert diags[0].severity.value == "warning"
    assert "DM214" not in _rules_fired('alpha="1" gamma="x" source="s"')


def test_engine_requires_fact_is_error_and_aggregates_with_other_phase1_errors() -> None:
    diags = _lint_synthetic('alpha="1" beta="2" delta="x"')
    assert any(diag.rule == "DM203" for diag in diags), diags
    requires = [diag for diag in diags if diag.rule == "DM214" and "delta" in diag.message]
    assert requires and requires[0].severity.value == "error", diags


def test_all_or_none_fact_lints_generically() -> None:
    assert "DM217" in _rules_fired('alpha="1" windowa="x"')  # partial group
    assert "DM217" not in _rules_fired('alpha="1" windowa="x" windowb="y"')
    assert "DM217" not in _rules_fired('alpha="1"')


def test_forbids_fact_lints_generically() -> None:
    assert "DM218" in _rules_fired('alpha="1" omega="no"')
    assert "DM218" not in _rules_fired('alpha="1"')


def test_valid_values_fact_lints_generically() -> None:
    assert "DM219" in _rules_fired('alpha="1" flavor="bitter"')
    assert "DM219" not in _rules_fired('alpha="1" flavor="sweet"')


def test_allowed_values_when_fact_lints_generically() -> None:
    assert "DM220" in _rules_fired('alpha="1" enabled="true" mode="unsafe"')
    assert "DM220" not in _rules_fired('alpha="1" enabled="true" mode="safe"')
    assert "DM220" not in _rules_fired('alpha="1" enabled="false" mode="unsafe"')


def test_mode_gated_facts_lint_generically() -> None:
    assert "DM205" in _rules_fired('alpha="1" source="s" kind="x" selector="y"')
    requires = [diag for diag in _lint_synthetic('alpha="1" shape="list"') if diag.rule == "DM221"]
    assert requires and requires[0].severity.value == "warning"
    assert "DM221" in _rules_fired('alpha="1" shape="literal" count="2"')
    assert "DM221" not in _rules_fired('alpha="1" shape="list" count="2"')


def test_nestedkey_default_guidance_is_warning_not_runtime_error() -> None:
    result = lint_source(
        '<setup rngSeed="1"><generate name="g" count="1">'
        "<nestedKey name=\"profile\" script=\"{'status': 'ok'}\"/>"
        "</generate></setup>"
    )
    guidance = [diag for diag in result.diagnostics if diag.rule == "DM214"]
    assert guidance and any("defaultValue" in diag.message for diag in guidance)
    assert all(diag.severity.value == "warning" for diag in guidance)
    assert result.ok


def test_dm204_uses_each_models_declared_distribution_policy() -> None:
    key_diags = _lint_rules_xml(
        '<setup rngSeed="1"><generate name="g" count="1">'
        '<key name="id" values="1,2" unique="true" distribution="shuffle"/>'
        "</generate></setup>"
    )
    key_unique = [diag for diag in key_diags if diag.rule == "DM204"]
    assert key_unique and "cannot be combined with 'distribution' on <key>" in key_unique[0].message

    reference_diags = _lint_rules_xml(
        '<setup rngSeed="1"><generate name="g" count="1">'
        '<reference name="customer_id" source="db" sourceType="customer" '
        'unique="true" distribution="ordered"/>'
        "</generate></setup>"
    )
    reference_unique = [diag for diag in reference_diags if diag.rule == "DM204"]
    assert reference_unique and "not 'ordered'" in reference_unique[0].message


def test_dm204_rejects_key_unique_weighted_source_before_runtime() -> None:
    diags = _lint_rules_xml(
        '<setup rngSeed="1"><generate name="g" count="1">'
        '<key name="segment" source="segments.wgt.csv" unique="true"/>'
        "</generate></setup>"
    )

    unique = [diag for diag in diags if diag.rule == "DM204"]
    assert unique and "requires 'values'" in unique[0].message


def test_schema_index_is_clean_after_gate() -> None:
    """The synthetic tag must not leak into the shared revision-cached index."""
    _lint_synthetic('alpha="1"')
    assert _TAG not in build_schema_index().tags


def test_rule_modules_have_no_model_specific_wiring() -> None:
    """Belt and braces: the rules must read facts from the schema index, never from
    specific model modules — a private constant import is exactly the P1 this gate kills."""
    from datamimic_ce.authoring.rules import best_practice, cross_statement, schema_rules, semantic_rules

    for module in (schema_rules, semantic_rules, best_practice, cross_statement):
        source = inspect.getsource(module)
        for model_module in (
            "model.key_model",
            "model.variable_model",
            "model.generate_model",
            "model.nested_key_model",
        ):
            assert model_module not in source, f"{module.__name__} imports from {model_module}"
