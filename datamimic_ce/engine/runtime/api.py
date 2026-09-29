"""Runtime-owned generator capabilities."""

from collections.abc import Iterator
from pathlib import Path
from typing import Literal

from datamimic_ce.domains.api import GeneratorCapability, describe_generator_type
from datamimic_ce.engine.dsl.api import parse_properties
from datamimic_ce.engine.runtime.contexts.context import Context, SetupContext
from datamimic_ce.engine.runtime.contracts import PlatformProperties, RunRequest, RunResult, RunSession
from datamimic_ce.engine.runtime.lifecycle.config import get_settings
from datamimic_ce.engine.runtime.lifecycle.runner import create_run_session as _create_run_session
from datamimic_ce.engine.runtime.lifecycle.runner import run as _run
from datamimic_ce.engine.runtime.tasks.values.construction.factory import RUNTIME_GENERATOR_TYPES


def iter_generator_capabilities() -> Iterator[GeneratorCapability]:
    for generator_type in RUNTIME_GENERATOR_TYPES:
        yield describe_generator_type(generator_type)


def runtime_environment() -> Literal["development", "production"]:
    return get_settings().RUNTIME_ENVIRONMENT


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
    "Context",
    "SetupContext",
    "create_run_session",
    "iter_generator_capabilities",
    "load_descriptor_properties",
    "run",
    "runtime_environment",
]
