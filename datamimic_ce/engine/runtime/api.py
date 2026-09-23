"""Runtime-owned generator capabilities."""

from collections.abc import Iterator
from typing import Literal

from datamimic_ce.engine.dsl.api import GeneratorCapability, describe_generator_type
from datamimic_ce.engine.runtime.config import settings
from datamimic_ce.engine.runtime.contracts import RunRequest, RunResult, RunSession
from datamimic_ce.engine.runtime.generators.sequence_table import SequenceTableGenerator
from datamimic_ce.engine.runtime.runner import create_run_session as _create_run_session
from datamimic_ce.engine.runtime.runner import run as _run


def iter_generator_capabilities() -> Iterator[GeneratorCapability]:
    yield describe_generator_type(SequenceTableGenerator)


def runtime_environment() -> Literal["development", "production"]:
    return settings.RUNTIME_ENVIRONMENT


def create_run_session(request: RunRequest) -> RunSession:
    return _create_run_session(request)


def run(request: RunRequest) -> RunResult:
    return _run(request)


__all__ = ["create_run_session", "iter_generator_capabilities", "run", "runtime_environment"]
