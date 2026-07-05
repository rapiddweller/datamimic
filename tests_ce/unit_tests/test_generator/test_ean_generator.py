# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

import pytest

from datamimic_ce.domains.common.literal_generators.ean_generator import EANGenerator


class TestEANGenerator:
    def test_generates_ean13(self):
        gen = EANGenerator(rng=random.Random(42))
        value = gen.generate()
        assert isinstance(value, str)
        assert len(value) == 13
        assert value.isdigit()

    def test_default_allows_repeats(self):
        gen = EANGenerator(rng=random.Random(1))
        # not asserting a collision (space is huge) - only that generate() never tracks state
        for _ in range(50):
            gen.generate()
        assert gen._seen == set()

    def test_unique_never_repeats(self):
        gen = EANGenerator(unique=True, rng=random.Random(7))
        values = [gen.generate() for _ in range(500)]
        assert len(values) == len(set(values))

    def test_unique_retries_then_fails_loudly(self):
        gen = EANGenerator(unique=True, rng=random.Random(3))
        # exhaust the space artificially: make the underlying generator constant
        gen._gen.generate = lambda: "4000000000000"  # type: ignore[method-assign]
        assert gen.generate() == "4000000000000"
        with pytest.raises(ValueError, match="no fresh EAN"):
            gen.generate()
