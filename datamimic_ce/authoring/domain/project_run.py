# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Request and result of running a project for its real output."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, StrictBool, StrictInt, StrictStr

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

    @classmethod
    def from_input_error(cls, message: str) -> ProjectRunResult:
        diagnostic = catalog_diagnostic(AuthoringRuleId.INPUT, message, phase=DiagnosticPhase.MODEL)
        return ProjectRunResult(outcome="not_run", diagnostics=(diagnostic,))


class ProjectRunExecution(AuthoringModel):
    """What the child process did, before the workflow names its outcome."""

    exit_code: StrictInt | None
    timed_out: StrictBool
    duration_seconds: float = Field(ge=0)
    artifacts: tuple[ProjectArtifact, ...]
    artifact_count: NonNegativeStrictInt
    log_tail: tuple[StrictStr, ...]
