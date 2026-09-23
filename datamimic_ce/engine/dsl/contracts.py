"""Typed values exposed across the DSL boundary."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratorCapability:
    name: str
    parameters: tuple[str, ...]
