"""Typed inputs and outputs for a runtime descriptor execution."""

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pydantic import RootModel

from datamimic_ce.engine.dsl.api import SetupStatement


class PlatformProperties(RootModel[dict[str, str]]):
    """Descriptor properties supplied by a transport."""


class PlatformConfiguration(RootModel[dict[str, object]]):
    """Runtime configuration values supplied by a transport."""


class CapturedProducts(RootModel[dict[str, list[dict[str, object]]]]):
    """Products captured by a test-mode execution."""


class FactoryConfig:
    """Configuration for generating a selected entity through the runtime."""

    def __init__(self, entity_name: str, count: int, custom_data: dict[str, object] | None = None):
        self._entity_name = entity_name
        self._count = count
        self._custom_data = custom_data

    @property
    def entity_name(self) -> str:
        return self._entity_name

    @property
    def count(self) -> int:
        return self._count

    @property
    def custom_data(self) -> dict[str, object] | None:
        return self._custom_data


StatementTransformer = Callable[[SetupStatement], None]


@dataclass(frozen=True)
class RunRequest:
    descriptor_path: Path
    task_id: str | None = None
    platform_props: PlatformProperties | None = None
    platform_configs: PlatformConfiguration | None = None
    test_mode: bool = False
    factory_config: FactoryConfig | None = None
    args: argparse.Namespace | None = None
    statement_transformer: StatementTransformer | None = None


@dataclass(frozen=True)
class RunResult:
    captured: CapturedProducts | None


class RunSession(Protocol):
    """Runtime-owned lifecycle for a single descriptor execution."""

    def execute(self) -> RunResult: ...

    def capture_test_result(self) -> CapturedProducts | None: ...
