"""Runtime-owned generator capabilities."""

from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from datamimic_ce.engine.dsl.api import GeneratorCapability, describe_generator_type, parse_properties
from datamimic_ce.engine.runtime.config import settings
from datamimic_ce.engine.runtime.contracts import PlatformProperties, RunRequest, RunResult, RunSession
from datamimic_ce.engine.runtime.generators.sequence_table import SequenceTableGenerator
from datamimic_ce.engine.runtime.runner import create_run_session as _create_run_session
from datamimic_ce.engine.runtime.runner import run as _run


def iter_generator_capabilities() -> Iterator[GeneratorCapability]:
    yield describe_generator_type(SequenceTableGenerator)


def runtime_environment() -> Literal["development", "production"]:
    return settings.RUNTIME_ENVIRONMENT


def load_descriptor_properties(descriptor_path: Path) -> PlatformProperties:
    properties_path = descriptor_path.parent / "conf/environment.env.properties"
    try:
        properties = parse_properties(properties_path)
    except FileNotFoundError:
        properties = {}
    return PlatformProperties.model_construct(root=properties)


def create_run_session(request: RunRequest) -> RunSession:
    return _create_run_session(request)


def run(request: RunRequest) -> RunResult:
    return _run(request)


__all__ = [
    "create_run_session",
    "iter_generator_capabilities",
    "load_descriptor_properties",
    "run",
    "runtime_environment",
]
