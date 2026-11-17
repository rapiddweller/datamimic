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
from .requests import BuildResult

MAX_PROJECT_RUN_SECONDS = 840
MAX_LISTED_ARTIFACTS = 200
LOG_TAIL_LINES = 50
_PARAM_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ExternalEffectKind(StrEnum):
    DATABASE = "database"
    MONGODB = "mongodb"
    EXECUTE = "execute"
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


class ProjectParam(AuthoringModel):
    """One runtime property NAME=VALUE handed to the run."""

    name: Annotated[StrictStr, Field(pattern=_PARAM_NAME.pattern)]
    value: StrictStr


class ProjectRunRequest(AuthoringModel):
    allow_side_effects: StrictBool = False
    params: tuple[ProjectParam, ...] = ()
    timeout_seconds: Annotated[StrictInt, Field(ge=1, le=MAX_PROJECT_RUN_SECONDS)] = 600


class ProjectRunResult(AuthoringModel):
    outcome: Literal["completed", "failed", "timeout", "not_run"]
    not_run_reason: Literal["input", "build_rejected", "side_effects_not_allowed"] | None = None
    build: BuildResult | None = None
    build_outcome: Literal["ready", "ready_with_gaps"] | None = Field(
        default=None, description="The outcome of the Build that preceded the run; absent when Build rejected."
    )
    coverage: BuildCoverage | None = Field(
        default=None, description="What that Build did not check. Fix each open gap before you report success."
    )
    action_required: str | None = Field(
        default=None, description="Set when the Build had open coverage gaps; do not report success until fixed."
    )
    required_side_effects: tuple[ExternalEffect, ...] = ()
    exit_code: StrictInt | None = None
    duration_seconds: float | None = Field(default=None, ge=0)
    artifacts: tuple[ProjectArtifact, ...] = ()
    artifact_count: NonNegativeStrictInt = 0
    log_tail: tuple[StrictStr, ...] = ()
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
                    self.build is not None
                    and self.build.outcome == "rejected"
                    and self.build_outcome is None
                    and self.coverage is None
                    and not self.required_side_effects
                    and not has_execution
                )
            else:
                valid = (
                    self.not_run_reason == "side_effects_not_allowed"
                    and self.build is None
                    and self.build_outcome is not None
                    and self.coverage is not None
                    and bool(self.required_side_effects)
                    and not has_execution
                )
        else:
            valid = (
                self.not_run_reason is None
                and self.build is None
                and self.build_outcome is not None
                and self.coverage is not None
                and not self.required_side_effects
                and self.duration_seconds is not None
                and (
                    (self.outcome == "completed" and self.exit_code == 0)
                    or (self.outcome == "failed" and self.exit_code is not None and self.exit_code != 0)
                    or (self.outcome == "timeout" and self.exit_code is None)
                )
            )
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
