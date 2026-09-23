"""Typed values exposed across the DSL boundary."""

from dataclasses import dataclass

StateTransitionRule = tuple[str, str, float]


@dataclass(frozen=True)
class GeneratorCapability:
    name: str
    parameters: tuple[str, ...]
