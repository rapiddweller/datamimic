"""Public domain generator types and capability projection."""

from collections.abc import Iterator

from datamimic_ce.domains.common.literal_generators.increment_generator import IncrementGenerator
from datamimic_ce.domains.common.literal_generators.state_transition_generator import (
    StateMachineDef,
    StateTransitionGenerator,
)
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.domain_core.generator_registry import generator_namespace
from datamimic_ce.engine.dsl.api import GeneratorCapability, describe_generator_type


def iter_generator_types() -> Iterator[type]:
    """Iterate the literal-generator classes available to runtime orchestration."""
    yield from generator_namespace().values()


def iter_generator_capabilities() -> Iterator[GeneratorCapability]:
    for generator_type in iter_generator_types():
        yield describe_generator_type(generator_type)


__all__ = [
    "BaseDomainGenerator",
    "BaseLiteralGenerator",
    "IncrementGenerator",
    "StateMachineDef",
    "StateTransitionGenerator",
    "iter_generator_capabilities",
    "iter_generator_types",
]
