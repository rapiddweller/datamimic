# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Base class for CE literal generators.

Literal generators produce primitive values (``str``, ``int``, ``datetime``,
…). Dataset-aware literal generators (``PhoneNumberGenerator``,
``GivenNameGenerator``, …) inherit from
:class:`datamimic_ce.domains.domain_core.base_domain_generator.DatasetAwareDomainGenerator`
instead of subclassing this — the tier hierarchy is universal, the
"literal vs domain" split is only about what ``.generate()`` returns.

This base owns only the RNG slot for atomic literal generators.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod


class BaseLiteralGenerator(ABC):
    """Base for atomic literal generators that need only an RNG."""

    # Generators are cached in the root context by default. Set
    # ``cache_in_root = False`` in subclasses to opt out of global caching.
    cache_in_root: bool = True

    # rng-driven output depends on the per-worker rng split, so under <setup rngSeed> these must run
    # single-process (see single_process_policy). Position-deterministic generators (increment/sequence)
    # override this to True.
    multiprocess_safe: bool = False

    def __init__(self, *, rng: random.Random | None = None) -> None:
        self._rng: random.Random = rng if rng is not None else random.Random()

    @property
    def rng(self) -> random.Random:
        return self._rng

    @rng.setter
    def rng(self, value: random.Random) -> None:
        # Lets the caller rebind a literal generator to a seeded rng (<setup rngSeed>) after construction.
        self._rng = value

    @abstractmethod
    def generate(self):
        """Generate a random literal value."""
        raise NotImplementedError("Subclasses must implement this method")
