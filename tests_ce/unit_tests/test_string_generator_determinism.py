# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Tests for deterministic behaviour of StringGenerator.rnd_str_from_regex."""

import random
import re

from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator


def _make_rng(seed: int) -> random.Random:
    return random.Random(seed)


class TestRndStrFromRegexDeterminism:
    """Same seed produces identical output; different seeds produce different output."""

    PATTERN = r"[A-Z]{4}US[A-Z0-9]{2}"

    def test_same_seed_same_output(self) -> None:
        """Running the same pattern with the same seeded rng yields the same string."""
        rng1 = _make_rng(42)
        rng2 = _make_rng(42)
        result1 = StringGenerator.rnd_str_from_regex(self.PATTERN, rng=rng1)
        result2 = StringGenerator.rnd_str_from_regex(self.PATTERN, rng=rng2)
        assert result1 == result2

    def test_same_seed_repeated_calls_are_stable(self) -> None:
        """Repeated calls with freshly seeded rngs always produce the same sequence."""
        pattern = r"[0-9]{4}"
        results_a = [StringGenerator.rnd_str_from_regex(pattern, rng=_make_rng(7)) for _ in range(10)]
        results_b = [StringGenerator.rnd_str_from_regex(pattern, rng=_make_rng(7)) for _ in range(10)]
        assert results_a == results_b

    def test_different_seeds_different_output(self) -> None:
        """Two distinct seeds should (overwhelmingly) produce different strings."""
        pattern = r"[A-Z0-9]{8}"
        outputs = {StringGenerator.rnd_str_from_regex(pattern, rng=_make_rng(seed)) for seed in range(20)}
        # With 36^8 possibilities and 20 tries, at least 5 distinct values is a conservative bound
        assert len(outputs) >= 5

    def test_no_rng_does_not_crash(self) -> None:
        """Calling without rng preserves backward compatibility and returns a valid string."""
        pattern = r"[A-Z]{3}[0-9]{3}"
        result = StringGenerator.rnd_str_from_regex(pattern)
        assert isinstance(result, str)
        assert re.fullmatch(pattern, result), f"Result '{result}' does not match pattern '{pattern}'"

    def test_result_matches_pattern(self) -> None:
        """Seeded output still conforms to the regex pattern."""
        pattern = r"[A-Z]{4}DE[A-Z0-9]{2}"
        for seed in range(5):
            result = StringGenerator.rnd_str_from_regex(pattern, rng=_make_rng(seed))
            assert re.fullmatch(pattern, result), f"Result '{result}' does not match '{pattern}'"

    def test_exrex_module_state_restored(self) -> None:
        """After a seeded call, the exrex module's choice/randint are restored."""
        import exrex  # type: ignore

        choice_before = exrex.choice
        randint_before = exrex.randint

        StringGenerator.rnd_str_from_regex(r"[A-Z]{4}", rng=_make_rng(99))

        assert exrex.choice is choice_before
        assert exrex.randint is randint_before
