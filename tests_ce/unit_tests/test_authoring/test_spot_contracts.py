# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Architecture contracts for the structural and business-rule SPOTs."""

import ast
from pathlib import Path

import pytest
from pydantic import BaseModel

from datamimic_ce.authoring.reference import capabilities_manifest, element_reference
from datamimic_ce.authoring.schema import build_schema_index, element_json_schema
from datamimic_ce.constants.element_constants import EL_GENERATE, EL_ITERATE
from datamimic_ce.enums.distribution_enums import NumberDistribution, SourceDistribution
from datamimic_ce.model.constraints import (
    KEY_DISTRIBUTION_VALUES,
    SOURCE_DISTRIBUTION_VALUES,
    Constraint,
    RequiredOneOf,
    element_constraints,
    registered_rule_tags,
    resolved_values,
    serialize_constraints,
)
from datamimic_ce.model.element_registry import (
    ElementDefinition,
    canonical_tag,
    get_element_definition,
    get_model_class,
    list_element_tags,
    register_element_extension,
    unregister_element_extension,
)


def test_structural_and_rule_registries_cover_the_same_ce_surface() -> None:
    assert registered_rule_tags() == frozenset(list_element_tags())


def test_builtin_models_select_rules_from_the_central_registry() -> None:
    for tag in list_element_tags():
        if canonical_tag(tag) != tag:
            continue
        model = get_model_class(tag)
        model_rules = getattr(model, "__constraints__", ()) if model is not None else ()
        assert model_rules == element_constraints(tag), f"<{tag}> model rules drifted from the rule registry"


def test_business_rules_only_reference_attributes_owned_by_their_model() -> None:
    """A central fact must not make CLI/MCP recommend an attribute the tag rejects."""
    for tag in list_element_tags():
        model = get_model_class(tag)
        if model is None:
            assert not element_constraints(tag)
            continue

        model_attributes = {field.alias or name for name, field in model.model_fields.items()}
        referenced: set[str] = set()
        for fact in element_constraints(tag):
            for collection_name in ("attrs", "needs", "excludes", "unless"):
                referenced.update(getattr(fact, collection_name, ()))
            for attribute_name in ("attr", "when_attr"):
                attribute = getattr(fact, attribute_name, None)
                if attribute is not None:
                    referenced.add(attribute)

        assert referenced <= model_attributes, (
            f"<{tag}> rules reference attributes outside its model: {sorted(referenced - model_attributes)}"
        )


def test_models_do_not_construct_business_rules_locally() -> None:
    constraint_types = {
        "RequiredOneOf",
        "MutuallyExclusive",
        "MutuallyExclusiveWhen",
        "Requires",
        "RequiresWhenValue",
        "AllOrNone",
        "Forbids",
        "ForbidsWhenValue",
        "ValidValues",
        "AllowedValuesWhen",
    }
    model_dir = Path(__file__).parents[3] / "datamimic_ce" / "model"
    violations: list[str] = []
    for path in sorted(model_dir.glob("*_model.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in constraint_types:
                violations.append(f"{path.name}:{node.lineno}:{node.func.id}")
    assert not violations, f"business rules must be declared in model/constraints.py only: {violations}"


def test_distribution_projections_use_the_central_runtime_derived_facts() -> None:
    manifest = capabilities_manifest()
    source_values = resolved_values(SOURCE_DISTRIBUTION_VALUES)
    number_values = resolved_values(KEY_DISTRIBUTION_VALUES)

    assert source_values == frozenset(member.value for member in SourceDistribution)
    assert number_values == frozenset(member.value for member in NumberDistribution)
    assert manifest["distributions"] == sorted(source_values)
    assert manifest["numeric_distributions"] == sorted(number_values)

    for tag in ("generate", "iterate", "variable", "nestedKey", "reference"):
        assert SOURCE_DISTRIBUTION_VALUES in element_constraints(tag)
    for tag in ("key", "id", "element"):
        assert KEY_DISTRIBUTION_VALUES in element_constraints(tag)


def test_schema_and_reference_project_alias_specific_central_rules() -> None:
    generate_rules = element_constraints(EL_GENERATE)
    iterate_rules = element_constraints(EL_ITERATE)
    assert iterate_rules != generate_rules

    expected = serialize_constraints(iterate_rules)
    index = build_schema_index()
    iterate_schema = index.get(EL_ITERATE)
    assert iterate_schema is not None and iterate_schema.constraints is iterate_rules
    assert capabilities_manifest()["elements"][EL_ITERATE]["constraints"] == expected
    assert element_json_schema(EL_ITERATE)["constraints"] == expected
    assert "at least one of: source" in element_reference(EL_ITERATE)


def test_extension_rules_are_registered_once_and_project_without_model_copies() -> None:
    tag = "synthetic-rule-spot"
    rules: tuple[Constraint, ...] = (RequiredOneOf(frozenset(("source",))),)

    class SyntheticModel(BaseModel):
        source: str | None = None

    register_element_extension(ElementDefinition(tag, SyntheticModel, None), rules)
    try:
        schema = build_schema_index().get(tag)
        assert schema is not None and schema.constraints is rules
        assert element_json_schema(tag)["constraints"] == serialize_constraints(rules)
    finally:
        unregister_element_extension(tag)


def test_extension_registration_rolls_back_structure_and_rules_atomically(monkeypatch: pytest.MonkeyPatch) -> None:
    from datamimic_ce.model.constraints import registry as rule_registry

    tag = "synthetic-atomic-extension"
    alias = "synthetic-atomic-alias"
    original_register = rule_registry._register_element_constraints

    def fail_for_alias(registered_tag: str, constraints: tuple[Constraint, ...]) -> None:
        if registered_tag == alias:
            raise RuntimeError("forced second-half failure")
        original_register(registered_tag, constraints)

    monkeypatch.setattr(rule_registry, "_register_element_constraints", fail_for_alias)

    with pytest.raises(RuntimeError, match="forced second-half failure"):
        register_element_extension(ElementDefinition(tag, None, None, aliases=frozenset({alias})))

    assert get_element_definition(tag) is None
    assert get_element_definition(alias) is None
    assert tag not in registered_rule_tags()
    assert alias not in registered_rule_tags()
