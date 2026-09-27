"""Shared contracts for domain generator metadata and transition rules."""

from dataclasses import dataclass

StateTransitionRule = tuple[str, str, float]


@dataclass(frozen=True)
class GeneratorCapability:
    name: str
    parameters: tuple[str, ...]
