# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Determinism contract for ``StringGenerator.rnd_str_from_regex``.

Pattern-level byte stability is already covered transitively by
``test_service_replay_determinism.py`` (Bank.bic / .bin uses this helper).
We keep only the regex-sampler-specific invariants here:

* Threading an ``rng`` makes the output reproducible.
* The exrex module's choice/randint are restored after the monkey-patch.
"""

import random

import pytest

from datamimic_ce.domains.common.literal_generators.string_generator import (
    StringGenerator,
    _exrex_using,
)


def test_seeded_rng_makes_regex_sampling_deterministic() -> None:
    result_a = StringGenerator.rnd_str_from_regex(r"[A-Z]{4}US[A-Z0-9]{2}", rng=random.Random(42))
    result_b = StringGenerator.rnd_str_from_regex(r"[A-Z]{4}US[A-Z0-9]{2}", rng=random.Random(42))
    assert result_a == result_b


def test_different_seeds_diverge() -> None:
    a = StringGenerator.rnd_str_from_regex(r"[A-Z0-9]{8}", rng=random.Random(42))
    b = StringGenerator.rnd_str_from_regex(r"[A-Z0-9]{8}", rng=random.Random(99))
    assert a != b


def test_exrex_module_state_is_restored_after_seeded_call() -> None:
    """The monkey-patch must not leak: a subsequent unseeded call must use
    the original module-level choice/randint."""
    import exrex  # type: ignore

    choice_before, randint_before = exrex.choice, exrex.randint
    StringGenerator.rnd_str_from_regex(r"[A-Z]{4}", rng=random.Random(99))
    assert exrex.choice is choice_before
    assert exrex.randint is randint_before


def test_exrex_using_swaps_only_within_the_block() -> None:
    """Inside the context exrex draws from the supplied rng; outside, the
    original module globals are in place."""
    import exrex  # type: ignore

    rng = random.Random(7)
    choice_before, randint_before = exrex.choice, exrex.randint

    with _exrex_using(rng):
        assert exrex.choice == rng.choice
        assert exrex.randint == rng.randint

    assert exrex.choice is choice_before
    assert exrex.randint is randint_before


def test_exrex_using_restores_state_when_body_raises() -> None:
    """Restoration must survive an exception in the wrapped call — this is the
    invariant the try/finally (now the context manager) exists to guarantee."""
    import exrex  # type: ignore

    choice_before, randint_before = exrex.choice, exrex.randint

    with pytest.raises(RuntimeError), _exrex_using(random.Random(1)):
        raise RuntimeError("boom inside the seam")

    assert exrex.choice is choice_before
    assert exrex.randint is randint_before


def test_exrex_using_none_is_a_true_noop() -> None:
    """rng=None must not touch exrex's module globals at all."""
    import exrex  # type: ignore

    choice_before, randint_before = exrex.choice, exrex.randint
    with _exrex_using(None):
        assert exrex.choice is choice_before
        assert exrex.randint is randint_before
    assert exrex.choice is choice_before
    assert exrex.randint is randint_before
