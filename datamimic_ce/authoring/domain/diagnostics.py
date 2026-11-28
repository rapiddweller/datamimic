# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Authoring diagnostics, rule identities, and their catalog entries."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, JsonValue, StrictStr, model_validator

from datamimic_ce.errors.catalog import get_issue_definition
from datamimic_ce.errors.codes import IssueCode
from datamimic_ce.errors.context import DescriptorLocation

from .common import AuthoringModel, NonEmptyStrictStr
from .expectations import ExpectationIntentKind
from .rule_catalog import RuleDefinition, RuleSeverity


class DiagnosticPhase(StrEnum):
    """Stable phase vocabulary shared by diagnostics and rejected builds."""

    MODEL = "model"
    EXPECTATION = "expectation"
    ENVIRONMENT_BINDING = "environment_binding"
    POLICY = "policy"
    COMPILE = "compile"
    DECOMPILE = "decompile"
    XML = "xml"
    EVIDENCE = "evidence"


class AuthoringRuleId(StrEnum):
    """Rule identities not already owned by a typed intent discriminator."""

    UNEVALUABLE_SINK_EXPECTATION = "unevaluable_sink_expectation"
    MISSING_EXPECTATION = "missing_expectation"
    COVERAGE_GAP = "coverage_gap"
    LIMIT = "limit"
    SIDE_EFFECT = "side_effect"
    INPUT = "input"
    VALIDATION = "validation"
    INCLUDE = "include"
    UNSUPPORTED_BOUNDED_OPERATION = "unsupported_bounded_operation"


class RuleOwner(StrEnum):
    EXPECTATION = "expectation"
    SAFETY = "safety"
    INPUT = "input"
    VALIDATION = "validation"
    TRANSPORT = "transport"


class AuthoringSystemDiagnosticCode(StrEnum):
    """Stable transport/runtime diagnostics that are not authoring rules."""

    DESCRIPTOR = "descriptor"
    CHILD_PARSE = "child_parse"
    CHILD_EXECUTION = "child_execution"
    CHILD_CRASH = "child_crash"
    CLEANUP = "cleanup"
    ENVIRONMENT = "environment"
    SERIALIZATION = "serialization"
    TIMEOUT = "timeout"
    NOT_EXECUTED = "not_executed"


class AuthoringBuildDiagnosticCode(StrEnum):
    """Stable build diagnostics that are neither catalog rules nor adapter failures."""

    CONFLICTING_ENVIRONMENT_DIRECTION = "conflicting_environment_direction"
    CONFLICTING_ENVIRONMENT_REFERENCE = "conflicting_environment_reference"
    CONFLICTING_ENVIRONMENT_TOPOLOGY = "conflicting_environment_topology"
    DUPLICATE_ENVIRONMENT_BINDING = "duplicate_environment_binding"
    ENVIRONMENT_FAMILY_MISMATCH = "environment_family_mismatch"
    UNKNOWN_ENVIRONMENT = "unknown_environment"
    UNSUPPORTED_CONSUMING_SOURCE_EVIDENCE = "unsupported_consuming_source_evidence"
    UNSUPPORTED_TARGET_ISOLATION = "unsupported_target_isolation"


class AuthoringCodecDiagnosticCode(StrEnum):
    """Stable failures owned by the reversible DM-JSON/XML codec boundary."""

    COMPILE_INVALID = "authoring_compile_invalid"
    DECOMPILE_UNSUPPORTED = "authoring_decompile_unsupported"


DmRuleId = Annotated[StrictStr, Field(pattern=r"^DM[0-9]{3}$")]


DiagnosticCode = (
    AuthoringRuleId
    | ExpectationIntentKind
    | AuthoringSystemDiagnosticCode
    | AuthoringBuildDiagnosticCode
    | AuthoringCodecDiagnosticCode
    | IssueCode
)


class DiagnosticLocation(AuthoringModel):
    file: str | None = None
    line: int | None = None
    column: int | None = None
    element: str | None = None
    name: str | None = None
    attribute: str | None = None
    include_chain: tuple[str, ...] = ()
    value_line: int | None = None
    value_column: int | None = None
    expression_line: int | None = None
    expression_column: int | None = None
    script_file: str | None = None
    script_line: int | None = None
    script_function: str | None = None


def diagnostic_location(location: DescriptorLocation | None) -> DiagnosticLocation | None:
    if location is None:
        return None
    return DiagnosticLocation(
        file=location.descriptor_path,
        line=location.line,
        column=location.column,
        element=location.element_tag,
        attribute=location.attribute,
        include_chain=location.include_chain,
    )


class Diagnostic(AuthoringModel):
    code: DiagnosticCode
    rule: DmRuleId | None = None
    message: NonEmptyStrictStr
    phase: DiagnosticPhase
    path: tuple[str | int, ...] = ()
    location: DiagnosticLocation | None = None
    expected: JsonValue | None = None
    actual: JsonValue | None = None
    allowed_values: tuple[JsonValue, ...] | None = None
    severity: Literal["error", "warning", "info"] = "error"
    remediation: NonEmptyStrictStr | None = None

    @classmethod
    def from_issue(
        cls,
        code: IssueCode,
        *,
        phase: DiagnosticPhase,
        message: str | None = None,
        remediation: str | None = None,
        path: tuple[str | int, ...] = (),
        location: DiagnosticLocation | None = None,
        expected: JsonValue | None = None,
        actual: JsonValue | None = None,
    ) -> Diagnostic:
        """Project a catalog issue without rendering exception text or location into the message."""
        definition = get_issue_definition(code)
        return cls(
            code=code,
            phase=phase,
            message=message or definition.cause,
            remediation=remediation or definition.resolution,
            severity="warning" if definition.severity == "warning" else "error",
            path=path,
            location=location,
            expected=expected,
            actual=actual,
        )

    @classmethod
    def from_rule(
        cls,
        definition: RuleDefinition,
        *,
        phase: DiagnosticPhase,
        path: tuple[str | int, ...],
        location: DiagnosticLocation | None = None,
        severity: RuleSeverity | None = None,
        names_only_fix: str | None = None,
        allowed_names: tuple[str, ...] | None = None,
    ) -> Diagnostic:
        """Project a DM rule, using the engine issue identity when it owns the same defect."""
        severity = severity or definition.severity
        return cls(
            code=definition.issue_code
            if definition.issue_code and severity is RuleSeverity.ERROR
            else AuthoringRuleId.VALIDATION,
            rule=definition.id,
            phase=phase,
            message=definition.explanation,
            path=path,
            location=location,
            severity="error"
            if severity is RuleSeverity.ERROR
            else ("warning" if severity is RuleSeverity.WARNING else "info"),
            remediation=f"{definition.fix_hint} {names_only_fix}" if names_only_fix else definition.fix_hint,
            allowed_values=allowed_names,
        )

    def relocated(self, path: tuple[str | int, ...]) -> Diagnostic:
        """The same finding at another path, e.g. inside an included step."""
        return self.model_copy(update={"path": path})

    @model_validator(mode="after")
    def errors_are_actionable(self) -> Diagnostic:
        if self.severity == "error" and self.remediation is None:
            raise ValueError("error diagnostics require remediation")
        return self


class RuleCatalogEntry(AuthoringModel):
    rule_id: AuthoringRuleId | ExpectationIntentKind | DmRuleId
    category: NonEmptyStrictStr
    severity: Literal["error", "warning", "info"]
    description: NonEmptyStrictStr
    applicability: NonEmptyStrictStr
    owner: RuleOwner
    remediation: NonEmptyStrictStr
    title: NonEmptyStrictStr | None = None
    provenance: NonEmptyStrictStr | None = None
    valid_example: NonEmptyStrictStr | None = None
    invalid_example: NonEmptyStrictStr | None = None
    advisory_severity: Literal["error", "warning", "hint"] | None = None
    blocks_verification: bool | None = None
