# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Contract tests for the three-tier domain generator hierarchy.

Pins what each tier adds and how its policy channels behave. End-to-end
byte-stability of real generators is gated by
``tests_ce/architecture/test_service_replay_determinism.py``.
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
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.domain_core.runtime.clock import DETERMINISTIC_ANCHOR


# ---------- BaseDomainGenerator -------------------------------------------


def test_base_seed_yields_seeded_mode_and_reproducible_rng() -> None:
    a = BaseDomainGenerator(seed=42)
    b = BaseDomainGenerator(seed=42)
    assert a.seeded_mode is True
    assert [a.rng.random() for _ in range(5)] == [b.rng.random() for _ in range(5)]


def test_base_no_args_is_unseeded() -> None:
    assert BaseDomainGenerator().seeded_mode is False


# ---------- DatasetAwareDomainGenerator -----------------------------------


@pytest.mark.parametrize(
    "given,expected",
    [(None, DEFAULT_DATASET), ("de", "DE"), ("DE", "DE"), ("us", "US")],
)
def test_normalize_dataset(given: str | None, expected: str) -> None:
    assert normalize_dataset(given) == expected


def test_dataset_aware_carries_rng_and_dataset() -> None:
    g = DatasetAwareDomainGenerator(seed=42, dataset="de")
    assert g.seeded_mode is True
    assert g.dataset == "DE"


# ---------- ClockAnchoredDomainGenerator ----------------------------------


def test_clock_anchored_seeded_uses_deterministic_anchor() -> None:
    assert ClockAnchoredDomainGenerator(seed=42).reference_now == DETERMINISTIC_ANCHOR


def test_clock_anchored_unseeded_uses_live_now() -> None:
    g = ClockAnchoredDomainGenerator()
    assert g.reference_now != DETERMINISTIC_ANCHOR
    assert isinstance(g.reference_now, datetime)


def test_clock_anchored_caller_reference_now_wins() -> None:
    custom = datetime(2030, 6, 15, 9, 0, 0)
    assert ClockAnchoredDomainGenerator(seed=42, reference_now=custom).reference_now == custom


def test_clock_anchored_reference_now_is_frozen_at_construction() -> None:
    g = ClockAnchoredDomainGenerator()
    assert g.reference_now is g.reference_now  # same identity on repeated reads


# ---------- seeded_mode error contract ------------------------------------


@pytest.mark.parametrize(
    "cls",
    [BaseDomainGenerator, DatasetAwareDomainGenerator, ClockAnchoredDomainGenerator],
)
def test_seeded_mode_true_without_source_raises(cls: type) -> None:
    with pytest.raises(ValueError, match="requires seed= or rng="):
        cls(seeded_mode=True)


# ---------- BaseLiteralGenerator ------------------------------------------


class _DummyLiteral(BaseLiteralGenerator):
    def generate(self) -> int:
        return self._rng.randint(0, 1_000_000)


def test_base_literal_caller_rng_is_kept_even_when_random_zero() -> None:
    """Regression test for ``rng or random.Random()`` falsy-bug.

    Random(0) can evaluate falsy under ``or`` in rare internal states;
    ``is not None`` is the only safe form.
    """
    src = random.Random(0)
    assert _DummyLiteral(rng=src).rng is src
