# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Drift gates for the central authoring-rule catalog and its projections."""

import ast
import inspect
from pathlib import Path

import pytest
from lxml import etree
from typer.testing import CliRunner

from datamimic_ce.authoring.contracts import ReferenceTopic
from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.reference import capabilities_manifest, reference
from datamimic_ce.authoring.rule_catalog import (
    AUTHORING_RULE_DEFINITIONS,
    RuleSeverity,
    authoring_rule_definitions,
    serialize_rule_definition,
)
from datamimic_ce.authoring.rules import ALL_INTENT_RULES, ALL_RULES
from datamimic_ce.authoring.rules.base import IntentLintContext, LintContext
from datamimic_ce.authoring.schema import build_schema_index
from datamimic_ce.cli import app
from datamimic_ce.enums.distribution_enums import POSITIONAL_NUMBER_SEQUENCES, NumberDistribution


def test_every_evaluator_points_to_exactly_one_complete_catalog_definition() -> None:
    definitions = authoring_rule_definitions()
    evaluators = (*ALL_RULES, *ALL_INTENT_RULES)
    assert len(definitions) == len(evaluators)
    assert len({definition.id for definition in definitions}) == len(definitions)
    assert {rule.definition for rule in evaluators} == set(definitions)

    for rule in evaluators:
        definition = rule.definition
        assert AUTHORING_RULE_DEFINITIONS[definition.id] is definition
        assert all(
            (
                definition.title,
                definition.explanation,
                definition.fix_hint,
                definition.provenance,
                definition.valid_example,
                definition.invalid_example,
            )
        )


def test_rule_severity_has_one_owner_and_catalog_is_immutable() -> None:
    assert Diagnostic.model_fields["severity"].annotation is RuleSeverity
    with pytest.raises(TypeError):
        AUTHORING_RULE_DEFINITIONS["DM999"] = authoring_rule_definitions()[0]  # type: ignore[index]


def test_evaluator_metadata_is_read_directly_from_definition() -> None:
    rule = ALL_RULES[0]
    assert set(rule.__dict__) & {"id", "severity", "docs"} == set()
    assert rule.definition in authoring_rule_definitions()


def test_public_evaluators_do_not_declare_identity_or_severity() -> None:
    rules_dir = Path(__file__).parents[3] / "datamimic_ce" / "authoring" / "rules"
    violations: list[str] = []
    for path in sorted(rules_dir.glob("*.py")):
        if path.name in {"__init__.py", "base.py"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                targets: list[ast.expr] = []
                if isinstance(statement, ast.Assign):
                    targets = statement.targets
                elif isinstance(statement, ast.AnnAssign):
                    targets = [statement.target]
                for target in targets:
                    if isinstance(target, ast.Name) and target.id in {"id", "severity", "docs"}:
                        violations.append(f"{path.name}:{statement.lineno}:{node.name}.{target.id}")
    assert not violations, f"rule identity/severity must come from RuleDefinition: {violations}"


def test_evaluators_cannot_replace_catalog_message_or_fix_hint() -> None:
    """Rule evaluators may add evidence, but cannot publish a parallel explanation."""
    parameters = inspect.signature(LintContext.diag).parameters
    assert "message" not in parameters
    assert "fix_hint" not in parameters
    intent_parameters = inspect.signature(IntentLintContext.diag).parameters
    assert "message" not in intent_parameters
    assert "fix_hint" not in intent_parameters

    rules_dir = Path(__file__).parents[3] / "datamimic_ce" / "authoring" / "rules"
    violations: list[str] = []
    for path in sorted(rules_dir.glob("*.py")):
        if path.name in {"__init__.py", "base.py"}:
            continue
        allowed_keywords = {"evidence", "fix_context", "severity"}
        if path.name == "intent_rules.py":
            allowed_keywords |= {"name", "path"}
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id == "Diagnostic":
                violations.append(f"{path.name}:{node.lineno}:direct Diagnostic construction")
            if not (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "ctx"
                and node.func.attr == "diag"
            ):
                continue
            if len(node.args) > 2:
                violations.append(f"{path.name}:{node.lineno}:positional diagnostic text")
            unexpected = {keyword.arg for keyword in node.keywords if keyword.arg is not None} - allowed_keywords
            if unexpected:
                violations.append(f"{path.name}:{node.lineno}:unexpected keywords {sorted(unexpected)}")
    assert not violations, f"evaluators must project catalog-owned diagnostics: {violations}"

    root = etree.fromstring(b"<setup/>")
    ctx = LintContext(root, build_schema_index())
    for rule in ALL_RULES:
        diagnostic = ctx.diag(
            rule,
            root,
            evidence="dynamic evidence",
            fix_context="Dynamic context.",
        )
        assert diagnostic.message.startswith(rule.definition.explanation)
        assert diagnostic.fix_hint.startswith(rule.definition.fix_hint)


def test_catalog_projects_identically_to_capabilities_and_reference() -> None:
    definitions = authoring_rule_definitions()
    assert capabilities_manifest()["rules"] == [serialize_rule_definition(item) for item in definitions]

    listing = reference(ReferenceTopic.RULES)
    for definition in definitions:
        assert f"{definition.id} [{definition.severity.value}]: {definition.title}" in listing
        detail = reference(ReferenceTopic.RULES, definition.id.lower())
        assert definition.explanation in detail
        assert definition.fix_hint in detail
        assert definition.provenance in detail

    cli_result = CliRunner().invoke(app, ["reference", "rules", "DM315"])
    assert cli_result.exit_code == 0
    assert "Severity: hint" in cli_result.stdout


def test_finite_sequence_projection_uses_runtime_enum_fact() -> None:
    expected = sorted(member.value for member in POSITIONAL_NUMBER_SEQUENCES)
    manifest = capabilities_manifest()
    assert manifest["finite_numeric_sequences"] == expected
    assert set(expected) < {member.value for member in NumberDistribution}
    distribution_reference = reference(ReferenceTopic.DISTRIBUTIONS)
    for value in expected:
        assert value in distribution_reference
