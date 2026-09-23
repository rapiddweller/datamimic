"""Runtime-facing domain generator types and registry."""

from collections.abc import Iterator

from datamimic_ce.domains.common.literal_generators.increment_generator import IncrementGenerator
from datamimic_ce.domains.common.literal_generators.state_transition_generator import (
    StateMachineDef,
    StateTransitionGenerator,
)
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.domain_core.generator_registry import generator_namespace


def iter_generator_types() -> Iterator[type]:
    """Iterate the literal-generator classes available to runtime orchestration."""
    yield from generator_namespace().values()

__all__ = [
    "BaseDomainGenerator",
    "BaseLiteralGenerator",
    "IncrementGenerator",
    "StateMachineDef",
    "StateTransitionGenerator",
    "iter_generator_types",
]
