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

Child generators are constructed by explicitly threading ``rng``,
``seeded_mode``, and ``dataset`` from parent to child::

    self._child = ChildGenerator(
        dataset=self._dataset,
        rng=self._rng,
        seeded_mode=self._seeded_mode,
    )

Subclasses access randomness through ``self.rng`` (a real
:class:`random.Random`) — no wrapper methods.
"""

from __future__ import annotations

import random
from datetime import datetime

from datamimic_ce.domains.domain_core.runtime import (
    now_utc_naive,
    resolve_clock,
    resolve_rng,
)

DEFAULT_DATASET = "US"


def normalize_dataset(dataset: str | None) -> str:
    """Normalise a dataset code: ``(dataset or DEFAULT_DATASET).upper()``.

    Single source of truth — when the implicit default moves, only this
    function changes.
    """
    return (dataset or DEFAULT_DATASET).upper()


class BaseDomainGenerator:
    """RNG-owning base for all CE domain generators.

    Subclasses must call ``super().__init__(rng=rng, seeded_mode=seeded_mode)``
    (and pass ``seed=`` if exposing it) so the resolved RNG / mode pair is
    stored on the instance.
    """

    def __init__(
        self,
        *,
        seed: int | None = None,
        rng: random.Random | None = None,
        seeded_mode: bool | None = None,
    ) -> None:
        self._rng, self._seeded_mode = resolve_rng(
            seed=seed, rng=rng, seeded_mode=seeded_mode
        )

    @property
    def rng(self) -> random.Random:
        return self._rng

    @property
    def seeded_mode(self) -> bool:
        return self._seeded_mode

    def _derive_rng(self) -> random.Random:
        """Spawn a deterministic child RNG from the current RNG state.

        Use when constructing nested generators that need an independent but
        reproducible stream.  Call sites are unchanged; subclass copies of
        this method should be deleted.
        """
        return random.Random(self._rng.randrange(2**63))


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
        seed: int | None = None,
        rng: random.Random | None = None,
        seeded_mode: bool | None = None,
    ) -> None:
        super().__init__(seed=seed, rng=rng, seeded_mode=seeded_mode)
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
        seed: int | None = None,
        rng: random.Random | None = None,
        seeded_mode: bool | None = None,
        reference_now: datetime | None = None,
    ) -> None:
        super().__init__(
            dataset=dataset, seed=seed, rng=rng, seeded_mode=seeded_mode
        )
        self._reference_now: datetime = (
            reference_now if reference_now is not None
            else resolve_clock(deterministic=self._seeded_mode)
        )

    @property
    def reference_now(self) -> datetime:
        return self._reference_now
