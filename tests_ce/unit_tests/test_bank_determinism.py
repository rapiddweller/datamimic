# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Tests for deterministic bic/bin generation in the Bank model."""

import random

from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.domains.finance.models.bank import Bank


def _make_bank(seed: int, dataset: str = "US") -> Bank:
    rng = random.Random(seed)
    generator = BankGenerator(dataset=dataset, rng=rng)
    return Bank(bank_generator=generator)


class TestBankDeterminism:
    """BIC and BIN are byte-identical for the same seed across runs."""

    def test_bic_same_seed_same_output(self) -> None:
        bank_a = _make_bank(seed=123)
        bank_b = _make_bank(seed=123)
        assert bank_a.bic == bank_b.bic

    def test_bin_same_seed_same_output(self) -> None:
        bank_a = _make_bank(seed=456)
        bank_b = _make_bank(seed=456)
        assert bank_a.bin == bank_b.bin

    def test_bic_different_seeds_different_output(self) -> None:
        bics = {_make_bank(seed=s).bic for s in range(20)}
        # With 26^4 * 36^2 possibilities, 20 seeds should yield at least 3 distinct BICs
        assert len(bics) >= 3

    def test_bin_different_seeds_different_output(self) -> None:
        bins = {_make_bank(seed=s).bin for s in range(20)}
        # BIN is [0-9]{4} — 10000 possibilities; expect several distinct values in 20 trials
        assert len(bins) >= 3

    def test_bic_embeds_dataset_country_code(self) -> None:
        """BIC for DE dataset must contain 'DE' in positions 4-5."""
        bank = _make_bank(seed=1, dataset="DE")
        assert bank.bic[4:6] == "DE", f"Expected 'DE' in BIC '{bank.bic}'"

    def test_bin_is_four_digits(self) -> None:
        bank = _make_bank(seed=7)
        assert bank.bin.isdigit() and len(bank.bin) == 4

    def test_multiple_seeds_bic_and_bin_deterministic(self) -> None:
        """End-to-end: rebuild generator with same seed → identical bic AND bin."""
        for seed in [0, 1, 42, 999, 12345]:
            b1 = _make_bank(seed)
            b2 = _make_bank(seed)
            assert b1.bic == b2.bic, f"BIC mismatch at seed {seed}"
            assert b1.bin == b2.bin, f"BIN mismatch at seed {seed}"
