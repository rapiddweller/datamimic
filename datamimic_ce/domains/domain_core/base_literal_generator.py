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

from datamimic_ce.domains.domain_core.runtime import ensure_rng


class BaseLiteralGenerator(ABC):
    """Base for atomic literal generators that need only an RNG."""

    # Generators are cached in the root context by default. Set
    # ``cache_in_root = False`` in subclasses to opt out of global caching.
    cache_in_root: bool = True

    def __init__(self, *, rng: random.Random | None = None) -> None:
        self._rng: random.Random = ensure_rng(rng)

    @property
    def rng(self) -> random.Random:
        return self._rng

    @abstractmethod
    def generate(self):
        """Generate a random literal value."""
        raise NotImplementedError("Subclasses must implement this method")
