# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.domains.common.literal_generators.ean_generator import EANGenerator


class TestEANGenerator:
    def test_generates_ean13(self):
        gen = EANGenerator(rng=random.Random(42))
        value = gen.generate()
        assert isinstance(value, str)
        assert len(value) == 13
        assert value.isdigit()

    def test_generate_is_stateless(self):
        """Generator produces values without tracking state.
        Cross-row dedup belongs to the task layer (unique=\"true\")."""
        gen = EANGenerator(rng=random.Random(1))
        values = [gen.generate() for _ in range(50)]
        assert len(values) == 50
        # No _seen set — generator is stateless after unique was removed
        assert not hasattr(gen, "_seen")

    def test_seeded_produces_reproducible_sequence(self):
        a = EANGenerator(rng=random.Random(42))
        b = EANGenerator(rng=random.Random(42))
        assert [a.generate() for _ in range(5)] == [b.generate() for _ in range(5)]
