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

from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator


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
