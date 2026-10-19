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
from pydantic import ValidationError
from typer.testing import CliRunner

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.build_rules import authoring_rule_catalog
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain
from datamimic_ce.authoring.domain.diagnostics import RuleCatalogEntry
from datamimic_ce.authoring.domain.requests import ReferenceRequest, ReferenceTopic
from datamimic_ce.authoring.domain.rule_catalog import (
    AUTHORING_RULE_DEFINITIONS,
    RuleSeverity,
    authoring_rule_definitions,
    serialize_rule_definition,
)
from datamimic_ce.authoring.domain.rules import ALL_RULES
from datamimic_ce.authoring.domain.rules.base import LintContext, Rule
from datamimic_ce.authoring.domain.schema import build_schema_index
from datamimic_ce.authoring.domain.xml_diagnostics import Diagnostic
from datamimic_ce.engine.dsl.vocabulary.enums.distribution_enums import POSITIONAL_NUMBER_SEQUENCES, NumberDistribution
from datamimic_ce.interfaces.cli import app


def test_every_evaluator_points_to_exactly_one_complete_catalog_definition() -> None:
    definitions = authoring_rule_definitions()
    evaluators = ALL_RULES
    assert definitions and evaluators
    assert len(definitions) == len(evaluators) + 1
    assert len({definition.id for definition in definitions}) == len(definitions)
    assert {rule.definition for rule in evaluators} | {AUTHORING_RULE_DEFINITIONS["DM407"]} == set(definitions)

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


def test_delivery_verification_blocking_is_central_rule_metadata() -> None:
    definition = AUTHORING_RULE_DEFINITIONS["DM407"]
    assert definition.blocks_verification is True
    assert serialize_rule_definition(definition)["blocks_verification"] is True
    result = create_authoring_application().reference(ReferenceRequest(topic=ReferenceTopic.RULES, name="DM407"))
    assert result.rules[0].blocks_verification is True
    assert result.rules[0].valid_example == definition.valid_example


def test_obsolete_intent_rule_ids_are_not_advertised() -> None:
    application = create_authoring_application()
    names = application.reference_names(ReferenceTopic.RULES)
    assert {"DM401", "DM402", "DM403", "DM405", "DM407"} <= set(names)
    assert not {"DM404", "DM406", "DM408"} & set(names)


def test_evaluator_metadata_is_read_directly_from_definition() -> None:
    rule = ALL_RULES[0]
    assert set(rule.__dict__) & {"id", "severity", "docs"} == set()
    assert rule.definition in authoring_rule_definitions()


def test_public_evaluators_do_not_declare_identity_or_severity() -> None:
    rules_dir = Path(inspect.getfile(Rule)).parent
    violations: list[str] = []
    paths = sorted(rules_dir.glob("*.py"))
    assert rules_dir.is_dir() and len(paths) >= 5
    assert {"schema_rules.py", "semantic_rules.py", "best_practice.py", "cross_statement.py"} <= {p.name for p in paths}
    for path in paths:
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

    rules_dir = Path(inspect.getfile(Rule)).parent
    violations: list[str] = []
    paths = sorted(rules_dir.glob("*.py"))
    assert rules_dir.is_dir() and len(paths) >= 5
    assert {"schema_rules.py", "semantic_rules.py", "best_practice.py", "cross_statement.py"} <= {p.name for p in paths}
    for path in paths:
        if path.name in {"__init__.py", "base.py"}:
            continue
        allowed_keywords = {"evidence", "fix_context", "severity"}
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
    ctx = LintContext(root, build_schema_index(), frozenset())
    for rule in ALL_RULES:
        diagnostic = ctx.diag(
            rule,
            root,
            evidence="dynamic evidence",
            fix_context="Dynamic context.",
        )
        assert diagnostic.message.startswith(rule.definition.explanation)
        assert diagnostic.fix_hint.startswith(rule.definition.fix_hint)


def test_catalog_projects_live_xml_and_build_rules_without_losing_metadata() -> None:
    application = create_authoring_application()
    listing = application.reference(ReferenceRequest(topic=ReferenceTopic.RULES))
    entries = {str(rule.rule_id): rule for rule in listing.rules}
    assert len(entries) == len(listing.rules)
    assert set(entries) == {item.id for item in authoring_rule_definitions()} | {
        str(item.rule_id) for item in authoring_rule_catalog()
    }
    for definition in authoring_rule_definitions():
        entry = entries[definition.id]
        assert entry.description == definition.explanation
        assert entry.remediation == definition.fix_hint
        assert entry.provenance == definition.provenance
        assert entry.title == definition.title
        assert entry.valid_example == definition.valid_example
        assert entry.invalid_example == definition.invalid_example
        assert entry.severity == ("info" if definition.severity is RuleSeverity.HINT else definition.severity.value)
        assert entry.blocks_verification == definition.blocks_verification
        assert entry.advisory_severity == (definition.advisory_severity.value if definition.advisory_severity else None)
        assert RuleCatalogEntry.model_validate_json(entry.model_dump_json()) == entry
        assert application.reference(ReferenceRequest(topic=ReferenceTopic.RULES, name=definition.id)).rules == (entry,)
    assert application.reference(ReferenceRequest(topic=ReferenceTopic.RULES, name="missing")).rules == ()
    cli_result = CliRunner().invoke(app, ["authoring", "reference", "--topic", "rules", "--name", "DM315"])
    assert cli_result.exit_code == 0
    import json

    assert json.loads(cli_result.stdout)["rules"][0]["severity"] == "info"


def test_finite_sequence_projection_uses_runtime_enum_fact() -> None:
    snapshot = create_authoring_application().capabilities()
    expected = {member.value for member in POSITIONAL_NUMBER_SEQUENCES}
    assert {item.name for item in snapshot.numeric_distributions if item.single_process_only} == expected
    assert set(snapshot.capability_names(CapabilityDomain.NUMERIC_DISTRIBUTION)) == {
        member.value for member in NumberDistribution
    }


@pytest.mark.parametrize("rule_id", ["DM12", "DM1000", "DM1ab", "made_up_rule", 401])
def test_catalog_identity_rejects_untyped_raw_codes(rule_id):
    entry = authoring_rule_catalog()[0].model_dump()
    entry["rule_id"] = rule_id
    with pytest.raises(ValidationError):
        RuleCatalogEntry.model_validate(entry)
