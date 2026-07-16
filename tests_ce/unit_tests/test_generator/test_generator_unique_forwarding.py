# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""unique="true" on <key>/<variable> with a generator: task-level dedup, not generator-owned."""

from datamimic_ce.domains.common.literal_generators.ean_generator import EANGenerator


class TestEANGenerator:
    def test_ean_generator_no_longer_owns_unique_flag(self) -> None:
        """unique was an antipattern on the generator — now at the task layer."""
        gen = EANGenerator(locale="en_US")
        # generate() just returns an EAN — no internal dedup
        assert gen.generate() is not None

    def test_ean_generator_produces_valid_ean(self) -> None:
        gen = EANGenerator()
        ean = gen.generate()
        assert len(str(ean)) == 13
        assert str(ean).isdigit()
