"""Runtime-owned generator capabilities."""

from collections.abc import Iterator

from datamimic_ce.engine.dsl.api import GeneratorCapability, describe_generator_type
from datamimic_ce.engine.runtime.generators.sequence_table import SequenceTableGenerator


def iter_generator_capabilities() -> Iterator[GeneratorCapability]:
    yield describe_generator_type(SequenceTableGenerator)


__all__ = ["iter_generator_capabilities"]
