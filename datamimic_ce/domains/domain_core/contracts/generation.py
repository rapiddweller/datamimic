"""Shared contracts for domain generator metadata and transition rules."""

from dataclasses import dataclass

StateTransitionRule = tuple[str, str, float]


@dataclass(frozen=True)
class StateMachineDef:
    """Immutable state-machine definition shared by domain transitions."""

    rules: tuple[StateTransitionRule, ...]
    start: str | None = None


@dataclass(frozen=True)
class GeneratorCapability:
    name: str
    parameters: tuple[str, ...]
