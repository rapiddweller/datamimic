# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Request and result of running a project for its real output."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr, model_validator

from .build_rules import catalog_diagnostic
from .common import AuthoringModel, NonEmptyStrictStr, NonNegativeStrictInt
from .coverage import BuildCoverage
from .diagnostics import AuthoringRuleId, Diagnostic, DiagnosticPhase
from .requests import BuildArtifact, RejectedBuild

MAX_PROJECT_RUN_SECONDS = 840
MAX_LISTED_ARTIFACTS = 200
LOG_TAIL_LINES = 50
_PARAM_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def run_outcome(exit_code: int | None) -> Literal["completed", "failed", "timeout"]:
    """The one outcome rule: no exit code means the run was stopped at its timeout."""
    return "timeout" if exit_code is None else "completed" if exit_code == 0 else "failed"


class ExternalEffectKind(StrEnum):
    DATABASE = "database"
    MONGODB = "mongodb"
    EXECUTE = "execute"
    # A createTable generate: the run creates the table client.entity when it is missing.
    SCHEMA = "schema"
    TARGET = "target"
    UNRESOLVED = "unresolved"


class ExternalEffect(AuthoringModel):
    """One statement of the project that reaches outside the project directory."""

    kind: ExternalEffectKind
    name: NonEmptyStrictStr
    descriptor: NonEmptyStrictStr


class ProjectArtifact(AuthoringModel):
    path: NonEmptyStrictStr
    bytes: NonNegativeStrictInt
    sha256: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")] | None = Field(
        default=None, description="Digest of the file after the run; absent when the file could not be read."
    )


class ProjectParam(AuthoringModel):
    """One runtime property NAME=VALUE handed to the run."""

    name: Annotated[StrictStr, Field(pattern=_PARAM_NAME.pattern)]
    value: StrictStr


class ProjectRunRequest(AuthoringModel):
    allow_side_effects: StrictBool = False
    params: tuple[ProjectParam, ...] = ()
    timeout_seconds: Annotated[StrictInt, Field(ge=1, le=MAX_PROJECT_RUN_SECONDS)] = 600


ProjectRunBuild = Annotated[
    RejectedBuild | BuildArtifact | None,
    Field(description="The Build artifact, or the full rejection if Build did not pass."),
]


# Spelled out in both results: ArchKeel decides an inline Literal, not an alias, as an API type.
# A test holds the two enums equal.
_NOT_RUN_REASON_DESCRIPTION = (
    "Why nothing ran: input (invalid project or options), build_rejected, side_effects_not_allowed, "
    "or confirmation_required (an unverified run that was not confirmed); null after a run."
)


class ProjectRunResult(AuthoringModel):
    outcome: Literal["completed", "failed", "timeout", "not_run"]
    not_run_reason: Literal["input", "build_rejected", "side_effects_not_allowed", "confirmation_required"] | None = (
        Field(default=None, description=_NOT_RUN_REASON_DESCRIPTION)
    )
    build: ProjectRunBuild = None
    build_outcome: Literal["ready", "ready_with_gaps"] | None = Field(
        default=None, description="The outcome of the Build that preceded the run; absent when Build rejected."
    )
    coverage: BuildCoverage | None = Field(
        default=None, description="What that Build did not check. Fix each open gap before you report success."
    )
    action_required: str | None = Field(
        default=None, description="Set when the Build had open coverage gaps; do not report success until fixed."
    )
    build_file_mismatches: tuple[NonEmptyStrictStr, ...] | None = Field(
        default=None,
        description="Build paths missing, unreadable or with different digests before or after execution. "
        "Empty means all digests matched at both checks; null means no comparison.",
    )
    required_side_effects: tuple[ExternalEffect, ...] = ()
    exit_code: StrictInt | None = None
    duration_seconds: float | None = Field(default=None, ge=0)
    artifacts: tuple[ProjectArtifact, ...] = ()
    artifact_count: NonNegativeStrictInt = 0
    log_tail: tuple[StrictStr, ...] = ()
    record_path: NonEmptyStrictStr | None = Field(
        default=None,
        description="Project-relative folder with run.json and the full run.log; absent when it could not be written.",
    )
    diagnostics: tuple[Diagnostic, ...] = ()

    @model_validator(mode="after")
    def consistent_outcome(self) -> ProjectRunResult:
        has_execution = any(
            (
                self.exit_code is not None,
                self.duration_seconds is not None,
                bool(self.artifacts),
                self.artifact_count != 0,
                bool(self.log_tail),
                self.build_file_mismatches is not None,
            )
        )
        if self.outcome == "not_run":
            if self.not_run_reason == "input":
                valid = (
                    self.build is None
                    and self.build_outcome is None
                    and self.coverage is None
                    and not self.required_side_effects
                    and not has_execution
                )
            elif self.not_run_reason == "build_rejected":
                valid = (
                    isinstance(self.build, RejectedBuild)
                    and self.build_outcome is None
                    and self.coverage is None
                    and not self.required_side_effects
                    and not has_execution
                )
            else:
                valid = (
                    self.not_run_reason == "side_effects_not_allowed"
                    and isinstance(self.build, BuildArtifact)
                    and self.build_outcome is not None
                    and self.coverage is not None
                    and bool(self.required_side_effects)
                    and not has_execution
                )
        else:
            valid = (
                self.not_run_reason is None
                and isinstance(self.build, BuildArtifact)
                and self.build_outcome is not None
                and self.build_file_mismatches is not None
                and self.coverage is not None
                and not self.required_side_effects
                and self.duration_seconds is not None
                and self.outcome == run_outcome(self.exit_code)
            )
        if (self.action_required is not None) != (self.build_outcome == "ready_with_gaps"):
            valid = False
        if not valid:
            raise ValueError("Project run outcome contradicts its execution and Build fields")
        return self

    @classmethod
    def from_input_error(cls, message: str) -> ProjectRunResult:
        diagnostic = catalog_diagnostic(AuthoringRuleId.INPUT, message, phase=DiagnosticPhase.MODEL)
        return ProjectRunResult(outcome="not_run", not_run_reason="input", diagnostics=(diagnostic,))


class ProjectRunExecution(AuthoringModel):
    """What the child process did, before the workflow names its outcome."""

    exit_code: StrictInt | None
    timed_out: StrictBool
    duration_seconds: float = Field(ge=0)
    artifacts: tuple[ProjectArtifact, ...]
    artifact_count: NonNegativeStrictInt
    log_tail: tuple[StrictStr, ...]
    record_path: NonEmptyStrictStr | None = None
    build_file_mismatches: tuple[NonEmptyStrictStr, ...] | None = None

    @model_validator(mode="after")
    def timeout_has_no_exit_code(self) -> ProjectRunExecution:
        if self.timed_out != (self.exit_code is None):
            raise ValueError("A run timed out exactly when it has no exit code")
        return self

    @property
    def outcome(self) -> Literal["completed", "failed", "timeout"]:
        return run_outcome(self.exit_code)


class ProjectRunRecord(AuthoringModel):
    """The audit record of one run (docs/runs/<start>_<task id>/run.json). docs/ is no Build input."""

    schema_version: Literal["1"] = "1"
    task_id: NonEmptyStrictStr
    actor: StrictStr | None
    started_utc: NonEmptyStrictStr
    ended_utc: NonEmptyStrictStr
    ce_version: NonEmptyStrictStr
    python_version: NonEmptyStrictStr
    param_names: tuple[StrictStr, ...] = Field(description="The names only: a value can be a secret.")
    proof: BuildArtifact | None = Field(description="The Build proof the run used; absent in an unverified run.")
    build_outcome: Literal["ready", "ready_with_gaps"] | None = None
    build_file_mismatches: tuple[NonEmptyStrictStr, ...] | None = None
    outcome: Literal["completed", "failed", "timeout"]
    exit_code: StrictInt | None
    duration_seconds: float = Field(ge=0)
    outputs: tuple[ProjectArtifact, ...]
    output_count: NonNegativeStrictInt
    log: NonEmptyStrictStr = Field(description="The full log, relative to the record folder.")


class UnverifiedProjectRunResult(AuthoringModel):
    verification: Literal["not_verified"] = "not_verified"
    outcome: Literal["not_run", "completed", "failed", "timeout"]
    not_run_reason: Literal["input", "build_rejected", "side_effects_not_allowed", "confirmation_required"] | None = (
        Field(default=None, description=_NOT_RUN_REASON_DESCRIPTION)
    )
    message: StrictStr
    execution: ProjectRunExecution | None = None
    details_truncated: StrictBool = False

    @model_validator(mode="after")
    def consistent_execution(self) -> UnverifiedProjectRunResult:
        if self.outcome == "not_run":
            # Build never runs here, so a rejected Build is no cause of this result.
            valid = self.execution is None and self.not_run_reason in (
                "input",
                "confirmation_required",
                "side_effects_not_allowed",
            )
        else:
            valid = (
                self.not_run_reason is None and self.execution is not None and self.execution.outcome == self.outcome
            )
        if not valid:
            raise ValueError("Unverified run outcome contradicts its execution")
        return self

    @classmethod
    def from_input_error(cls, message: str) -> UnverifiedProjectRunResult:
        return UnverifiedProjectRunResult(outcome="not_run", not_run_reason="input", message=message)
