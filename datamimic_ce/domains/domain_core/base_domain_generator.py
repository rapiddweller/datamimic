# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Base classes for CE domain generators.

Three tiers, picked by what the generator actually needs:

* :class:`BaseDomainGenerator` — RNG only. For atomic generators with no
  dataset and no "now"-derived fields.
* :class:`DatasetAwareDomainGenerator` — adds normalised dataset code.
* :class:`ClockAnchoredDomainGenerator` — adds a frozen reference clock
  for entities whose fields are derived from "now" (founding year, age,
  transaction date, …). Anchored once at construction so all year-derived
  fields on a single entity are mutually consistent.

Determinism is a single channel: pass a ``rng`` and the run is
deterministic (seeded); pass nothing and it is not. There is no separate
``seeded_mode`` flag — "was an rng supplied" is the policy. Nested
generators are constructed by threading :meth:`_derive_rng`::

    self._child = ChildGenerator(dataset=self._dataset, rng=self._derive_rng())

In a seeded run ``_derive_rng`` forks a reproducible child RNG; in an
unseeded run it returns ``None`` so the child seeds itself from the wall
clock — keeping the child's mode identical to the parent's.

Subclasses access randomness through ``self.rng`` — no wrapper methods.
"""

from __future__ import annotations

import random
from datetime import datetime

from datamimic_ce.domains.domain_core.runtime import resolve_clock, spawn_rng

DEFAULT_DATASET = "US"


def normalize_dataset(dataset: str | None) -> str:
    """Normalise a dataset code: ``(dataset or DEFAULT_DATASET).upper()``.

    Single source of truth — when the implicit default moves, only this
    function changes.
    """
    return (dataset or DEFAULT_DATASET).upper()


class BaseDomainGenerator:
    """RNG-owning base for all CE domain generators.

    Subclasses must call ``super().__init__(rng=rng)``. Passing a ``rng``
    marks the instance seeded (deterministic); passing ``None`` makes it
    unseeded with a fresh wall-clock-seeded Random.
    """

    def __init__(self, *, rng: random.Random | None = None) -> None:
        self._seeded: bool = rng is not None
        self._rng: random.Random = rng if rng is not None else random.Random()

    @property
    def rng(self) -> random.Random:
        return self._rng

    @property
    def seeded(self) -> bool:
        return self._seeded

    def _derive_rng(self) -> random.Random | None:
        """Fork a child RNG that inherits this generator's determinism.

        Seeded → a reproducible child Random derived from the parent state.
        Unseeded → ``None`` so the child seeds itself from the wall clock,
        keeping the child in the same (unseeded) mode as the parent.
        """
        return spawn_rng(self._rng) if self._seeded else None


class DatasetAwareDomainGenerator(BaseDomainGenerator):
    """Domain generator with a normalised dataset code.

    Centralises ``(dataset or "US").upper()`` so the implicit default lives
    in one place. Use this tier for any generator that resolves dataset-
    suffixed CSV assets.
    """

    def __init__(
        self,
        *,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ) -> None:
        super().__init__(rng=rng)
        self._dataset = normalize_dataset(dataset)

    @property
    def dataset(self) -> str:
        return self._dataset


class ClockAnchoredDomainGenerator(DatasetAwareDomainGenerator):
    """Dataset-aware generator that also anchors a reference clock once.

    Use when any field is derived from "now" (founding year, age,
    expiration date, …). The anchor is captured **once** at construction
    time so every "now"-derived field on the same entity references the
    same instant — under a seeded run that's the
    :data:`DETERMINISTIC_ANCHOR`, under an unseeded run it's wall-clock at
    construction time.
    """

    def __init__(
        self,
        *,
        dataset: str | None = None,
        rng: random.Random | None = None,
        reference_now: datetime | None = None,
    ) -> None:
        super().__init__(dataset=dataset, rng=rng)
        self._reference_now: datetime = (
            reference_now if reference_now is not None else resolve_clock(deterministic=self._seeded)
        )

    @property
    def reference_now(self) -> datetime:
        return self._reference_now
