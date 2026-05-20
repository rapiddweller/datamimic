"""Tests pinning the three-tier domain generator hierarchy contract.

* :class:`BaseDomainGenerator` — RNG only.
* :class:`DatasetAwareDomainGenerator` — adds normalised dataset.
* :class:`ClockAnchoredDomainGenerator` — adds frozen reference_now.

Plus :class:`BaseLiteralGenerator` — RNG slot for atomic literal
generators, with the ``Random(0)`` falsy-bug fix verified.
"""

from __future__ import annotations

import random
from datetime import datetime

import pytest

from datamimic_ce.domains.domain_core.base_domain_generator import (
    DEFAULT_DATASET,
    BaseDomainGenerator,
    ClockAnchoredDomainGenerator,
    DatasetAwareDomainGenerator,
    normalize_dataset,
)
from datamimic_ce.domains.domain_core.base_literal_generator import (
    BaseLiteralGenerator,
)
from datamimic_ce.domains.domain_core.runtime.clock import DETERMINISTIC_ANCHOR


# ---------- BaseDomainGenerator -------------------------------------------


def test_base_domain_generator_exposes_rng_and_seeded_mode() -> None:
    g = BaseDomainGenerator(seed=42)
    assert isinstance(g.rng, random.Random)
    assert g.seeded_mode is True


def test_base_domain_generator_no_args_is_unseeded() -> None:
    g = BaseDomainGenerator()
    assert g.seeded_mode is False


def test_base_domain_generator_same_seed_is_byte_identical() -> None:
    a = BaseDomainGenerator(seed=42)
    b = BaseDomainGenerator(seed=42)
    assert [a.rng.random() for _ in range(5)] == [b.rng.random() for _ in range(5)]


# ---------- DatasetAwareDomainGenerator -----------------------------------


def test_dataset_aware_default_is_us_uppercase() -> None:
    g = DatasetAwareDomainGenerator()
    assert g.dataset == "US"


def test_dataset_aware_lowercases_input_to_uppercase() -> None:
    g = DatasetAwareDomainGenerator(dataset="de")
    assert g.dataset == "DE"


def test_dataset_aware_carries_rng_through() -> None:
    g = DatasetAwareDomainGenerator(seed=42, dataset="DE")
    assert g.seeded_mode is True
    assert g.dataset == "DE"


def test_normalize_dataset_helper() -> None:
    assert normalize_dataset(None) == DEFAULT_DATASET
    assert normalize_dataset("de") == "DE"
    assert normalize_dataset("DE") == "DE"


# ---------- ClockAnchoredDomainGenerator ----------------------------------


def test_clock_anchored_seeded_uses_deterministic_anchor() -> None:
    g = ClockAnchoredDomainGenerator(seed=42)
    assert g.reference_now == DETERMINISTIC_ANCHOR


def test_clock_anchored_unseeded_uses_live_now() -> None:
    g = ClockAnchoredDomainGenerator()
    assert g.reference_now != DETERMINISTIC_ANCHOR
    assert isinstance(g.reference_now, datetime)


def test_clock_anchored_caller_supplied_reference_wins() -> None:
    custom = datetime(2030, 6, 15, 9, 0, 0)
    g = ClockAnchoredDomainGenerator(seed=42, reference_now=custom)
    assert g.reference_now == custom


def test_clock_anchored_reference_now_is_frozen_at_construction() -> None:
    """The reference must NOT advance when read multiple times."""
    g = ClockAnchoredDomainGenerator()
    first = g.reference_now
    second = g.reference_now
    assert first is second


def test_clock_anchored_two_seeded_instances_share_anchor() -> None:
    """Seeded entities produced same-seed share the DETERMINISTIC_ANCHOR."""
    a = ClockAnchoredDomainGenerator(seed=42, dataset="US")
    b = ClockAnchoredDomainGenerator(seed=42, dataset="US")
    assert a.reference_now == b.reference_now == DETERMINISTIC_ANCHOR


# ---------- BaseLiteralGenerator ------------------------------------------


class _DummyLiteral(BaseLiteralGenerator):
    def generate(self) -> int:
        return self._rng.randint(0, 1_000_000)


def test_base_literal_default_init_works() -> None:
    g = _DummyLiteral()
    assert isinstance(g.rng, random.Random)


def test_base_literal_caller_rng_is_kept() -> None:
    src = random.Random(7)
    g = _DummyLiteral(rng=src)
    assert g.rng is src


def test_base_literal_random_zero_seeded_rng_is_not_silently_replaced() -> None:
    """Regression test for the ``rng or random.Random()`` falsy-bug.

    Random(0) in some internal states evaluates falsy under ``or``; using
    ``is not None`` is the only safe form. This locks the fix.
    """
    src = random.Random(0)
    g = _DummyLiteral(rng=src)
    assert g.rng is src


# ---------- seeded_mode error contract ------------------------------------


def test_dataset_aware_seeded_mode_true_without_source_raises() -> None:
    with pytest.raises(ValueError, match="requires seed= or rng="):
        DatasetAwareDomainGenerator(seeded_mode=True)


def test_clock_anchored_seeded_mode_true_without_source_raises() -> None:
    with pytest.raises(ValueError, match="requires seed= or rng="):
        ClockAnchoredDomainGenerator(seeded_mode=True)
