# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Authoring diagnostics, rule identities, and their catalog entries."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, JsonValue, StrictStr, model_validator

from datamimic_ce.errors.codes import ErrorCode, IssueCode

from .common import AuthoringModel, NonEmptyStrictStr
from .expectations import ExpectationIntentKind


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

    UNASSURED_MULTI_CONTRIBUTOR_SINK = "unassured_multi_contributor_sink"
    UNEVALUABLE_SINK_EXPECTATION = "unevaluable_sink_expectation"
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
    ASSERT_FAILED = "assert_failed"


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


RawXmlDiagnosticCode = Annotated[StrictStr, Field(pattern=r"^DM[0-9]{3}$")]


DiagnosticCode = (
    AuthoringRuleId
    | ExpectationIntentKind
    | AuthoringSystemDiagnosticCode
    | AuthoringBuildDiagnosticCode
    | AuthoringCodecDiagnosticCode
    | RawXmlDiagnosticCode
)


class CeErrorIdentity(AuthoringModel):
    """Machine-readable identity of one catalog-backed CE error."""

    error_code: ErrorCode
    issue_code: IssueCode | None = None


class Diagnostic(AuthoringModel):
    code: DiagnosticCode
    message: NonEmptyStrictStr
    phase: DiagnosticPhase
    path: tuple[str | int, ...] = ()
    expected: JsonValue | None = None
    actual: JsonValue | None = None
    allowed_values: tuple[JsonValue, ...] | None = None
    severity: Literal["error", "warning", "info"] = "error"
    remediation: NonEmptyStrictStr | None = None
    ce_error: CeErrorIdentity | None = None

    def relocated(self, path: tuple[str | int, ...]) -> Diagnostic:
        """The same finding at another path, e.g. inside an included step."""
        return self.model_copy(update={"path": path})

    @model_validator(mode="after")
    def errors_are_actionable(self) -> Diagnostic:
        if self.severity == "error" and self.remediation is None:
            raise ValueError("error diagnostics require remediation")
        return self


class RuleCatalogEntry(AuthoringModel):
    rule_id: AuthoringRuleId | ExpectationIntentKind | RawXmlDiagnosticCode
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
