"""Neutral random-source contract and sampling helpers shared across layers."""

from __future__ import annotations

import random
from collections.abc import MutableSequence, Sequence
from typing import Protocol, TypeVar

T = TypeVar("T")


class RandomSource(Protocol):
    def randint(self, a: int, b: int) -> int: ...
    def random(self) -> float: ...
    def uniform(self, a: float, b: float) -> float: ...
    def randbytes(self, n: int) -> bytes: ...
    def getrandbits(self, k: int) -> int: ...
    def choice(self, seq: Sequence[T]) -> T: ...
    def choices(
        self,
        population: Sequence[T],
        weights: Sequence[float] | None = None,
        *,
        cum_weights: Sequence[float] | None = None,
        k: int = 1,
    ) -> list[T]: ...
    def shuffle(self, x: MutableSequence[T]) -> None: ...


def cumulated_index(rng: random.Random, span: int) -> int:
    """Return an index selected with a symmetric bell-shaped distribution."""
    return (sum(rng.randint(0, span) for _ in range(5)) + 2) // 5
