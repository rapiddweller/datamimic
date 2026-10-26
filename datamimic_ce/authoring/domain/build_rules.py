# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Catalog and diagnostics for rules emitted by the public Authoring workflow."""

from __future__ import annotations

from pydantic import JsonValue

from datamimic_ce.authoring.domain.diagnostics import (
    AuthoringRuleId,
    Diagnostic,
    DiagnosticPhase,
    RuleCatalogEntry,
    RuleOwner,
)
from datamimic_ce.authoring.domain.expectations import ExpectationIntentKind

AUTHORING_RULE_CATALOG: tuple[RuleCatalogEntry, ...] = (
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.EXACT_COUNT,
        category="expectation",
        severity="error",
        description="Captured product rows must match the requested exact count.",
        applicability="Explicit or derived exact-count expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Adjust the product count or generation intent to produce the requested number of rows.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.PER_PARENT_COUNT,
        category="expectation",
        severity="error",
        description="Each parent must have the requested number of child rows.",
        applicability="Explicit or derived nested relationship count expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Adjust the nested child count or relationship intent for every parent.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.UNIQUE,
        category="expectation",
        severity="error",
        description="Captured values must be unique within the declared scope.",
        applicability="Explicit or derived unique-field expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Use a generator and scope that cannot emit duplicate field values.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.FOREIGN_KEY,
        category="expectation",
        severity="error",
        description="Captured child foreign-key values must reference captured parent values.",
        applicability="Explicit or derived foreign-key expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Correct the child relationship field so every key references a parent row.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.ALLOWED_VALUES,
        category="expectation",
        severity="error",
        description="Captured field values must belong to the declared allowed set.",
        applicability="Explicit or derived allowed-values expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Constrain the field generator to the declared allowed values.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.RANGE,
        category="expectation",
        severity="error",
        description="Captured numeric values must remain within the declared range.",
        applicability="Explicit range expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Adjust the field range or generator bounds to fit the expectation.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.FIXED_VALUE,
        category="expectation",
        severity="error",
        description="Every captured value must equal the declared fixed value.",
        applicability="Explicit fixed-value expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Use a constant field or adjust the expected value to match the required model semantics.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.FIELD_PRESENT,
        category="expectation",
        severity="error",
        description="Every captured row must contain the declared field.",
        applicability="Explicit required-field expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Declare and populate the required field in every row.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.FIELD_ABSENT,
        category="expectation",
        severity="error",
        description="No captured row may contain the declared field.",
        applicability="Explicit forbidden-field expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Remove the forbidden field from the product model.",
    ),
    RuleCatalogEntry(
        rule_id=ExpectationIntentKind.ROW_CONDITION,
        category="expectation",
        severity="error",
        description="Every captured row must satisfy its declared condition.",
        applicability="Explicit row-condition expectations.",
        owner=RuleOwner.EXPECTATION,
        remediation="Change the row condition or generation intent so every row satisfies it.",
    ),
    RuleCatalogEntry(
        rule_id=AuthoringRuleId.UNASSURED_MULTI_CONTRIBUTOR_SINK,
        category="expectation",
        severity="warning",
        description="Multiple products share a declared sink without any sink-scoped assurance.",
        applicability="Supported declared insert sinks with more than one contributing product.",
        owner=RuleOwner.EXPECTATION,
        remediation="Add an expectation whose subject names the declared sink and the required cross-product rule.",
    ),
    RuleCatalogEntry(
        rule_id=AuthoringRuleId.UNEVALUABLE_SINK_EXPECTATION,
        category="expectation",
        severity="error",
        description="A declared-sink expectation requires complete bounded capture for every contributing product.",
        applicability="Explicit expectations evaluated over a declared-sink row union.",
        owner=RuleOwner.EXPECTATION,
        remediation="Repair bounded generation so every declared-sink contributor is captured before evaluation.",
    ),
    RuleCatalogEntry(
        rule_id=AuthoringRuleId.LIMIT,
        category="safety",
        severity="error",
        description="Build evidence requires finite counts and complete capture within the configured limits.",
        applicability="Counts, processes, nested expansion, and source-driven authoring execution.",
        owner=RuleOwner.SAFETY,
        remediation=(
            "Use finite generation within max_count; keep all capture and acceptance requirements satisfiable."
        ),
    ),
    RuleCatalogEntry(
        rule_id=AuthoringRuleId.SIDE_EFFECT,
        category="safety",
        severity="error",
        description="Dry-run execution must reject write-capable descriptor elements.",
        applicability="Bounded execution with side effects disabled.",
        owner=RuleOwner.SAFETY,
        remediation="Use run with explicit side-effect permission or remove write-capable elements.",
    ),
    RuleCatalogEntry(
        rule_id=AuthoringRuleId.INPUT,
        category="input",
        severity="error",
        description="Authoring commands require input matching the selected typed operation.",
        applicability="Application requests with missing or malformed DM JSON, build, or XML input.",
        owner=RuleOwner.INPUT,
        remediation="Provide the complete typed payload through the selected operation's declared input channel.",
    ),
    RuleCatalogEntry(
        rule_id=AuthoringRuleId.VALIDATION,
        category="validation",
        severity="error",
        description="Authoring payloads must satisfy the versioned DM JSON or BuildRequestV5 contract.",
        applicability="JSON authoring payload validation.",
        owner=RuleOwner.VALIDATION,
        remediation="Correct the reported field, discriminator, or graph reference.",
    ),
    RuleCatalogEntry(
        rule_id=AuthoringRuleId.INCLUDE,
        category="transport",
        severity="error",
        description="Bounded Authoring proof requires a contained, finite, literal project dependency graph.",
        applicability="Dynamic, missing, escaping, cyclic, malformed, or excessive include dependencies.",
        owner=RuleOwner.TRANSPORT,
        remediation=(
            "Use literal relative XML or properties paths inside the descriptor directory and keep the dependency "
            "graph within the published bounded workspace limits."
        ),
    ),
    RuleCatalogEntry(
        rule_id=AuthoringRuleId.UNSUPPORTED_BOUNDED_OPERATION,
        category="safety",
        severity="error",
        description="Bounded Authoring proof rejects operations without a bounded evidence mode.",
        applicability="Runtime operations such as model training and artifact generation.",
        owner=RuleOwner.SAFETY,
        remediation=(
            "Remove the operation from bounded Authoring proof and validate it through its dedicated runtime workflow."
        ),
    ),
)


def authoring_rule_catalog() -> tuple[RuleCatalogEntry, ...]:
    return AUTHORING_RULE_CATALOG


_RULES_BY_ID = {rule.rule_id: rule for rule in AUTHORING_RULE_CATALOG}


def catalog_diagnostic(
    rule_id: AuthoringRuleId | ExpectationIntentKind,
    message: str,
    *,
    phase: DiagnosticPhase,
    path: tuple[str | int, ...] = (),
    expected: JsonValue | None = None,
    actual: JsonValue | None = None,
    allowed_values: tuple[JsonValue, ...] | None = None,
    remediation: str | None = None,
) -> Diagnostic:
    """A catalog finding; ``remediation`` replaces the rule's generic fix when the caller knows the specific one."""
    rule = _RULES_BY_ID[rule_id]
    return Diagnostic(
        code=rule.rule_id,
        message=message,
        phase=phase,
        path=path,
        expected=expected,
        actual=actual,
        allowed_values=allowed_values,
        severity=rule.severity,
        remediation=remediation or rule.remediation,
    )
