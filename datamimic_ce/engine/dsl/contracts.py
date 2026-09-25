"""Typed values exposed across the DSL boundary."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class EntityValue(ABC):
    @abstractmethod
    def to_dict(self) -> dict[str, object]: ...

StateTransitionRule = tuple[str, str, float]


@dataclass(frozen=True)
class GeneratorCapability:
    name: str
    parameters: tuple[str, ...]
