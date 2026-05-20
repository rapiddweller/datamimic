# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Clock determinism tests for CE generators.

For each fixed generator, verify:
1. Same seed + same reference_now  -> byte-identical date/time fields
2. Same seed + different reference_now -> output diverges
3. No reference_now supplied -> still works (live wall-clock path)
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import pytest

from datamimic_ce.domains.domain_core.runtime.clock import DETERMINISTIC_ANCHOR


# ---------------------------------------------------------------------------
# BankAccountGenerator
# ---------------------------------------------------------------------------

class TestBankAccountGeneratorClockDeterminism:
    def _make(self, seed: int, reference_now: datetime | None) -> object:
        from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator

        return BankAccountGenerator(rng=random.Random(seed), reference_now=reference_now)

    def test_same_seed_same_reference_now_gives_identical_dates(self) -> None:
        g1 = self._make(42, DETERMINISTIC_ANCHOR)
        g2 = self._make(42, DETERMINISTIC_ANCHOR)
        d1 = g1.generate_created_date()
        d2 = g2.generate_created_date()
        assert d1 == d2

    def test_same_seed_different_reference_now_diverges(self) -> None:
        anchor_a = DETERMINISTIC_ANCHOR
        anchor_b = DETERMINISTIC_ANCHOR + timedelta(days=60)
        g1 = self._make(42, anchor_a)
        g2 = self._make(42, anchor_b)
        d1 = g1.generate_created_date()
        d2 = g2.generate_created_date()
        assert d1 != d2

    def test_no_reference_now_still_works(self) -> None:
        g = self._make(42, None)
        result = g.generate_created_date()
        assert isinstance(result, datetime)


# ---------------------------------------------------------------------------
# TransactionGenerator
# ---------------------------------------------------------------------------

class TestTransactionGeneratorClockDeterminism:
    def _make(self, seed: int, reference_now: datetime | None) -> object:
        from datamimic_ce.domains.finance.generators.transaction_generator import TransactionGenerator

        return TransactionGenerator(rng=random.Random(seed), reference_now=reference_now)

    def test_same_seed_same_reference_now_gives_identical_dates(self) -> None:
        g1 = self._make(7, DETERMINISTIC_ANCHOR)
        g2 = self._make(7, DETERMINISTIC_ANCHOR)
        assert g1.generate_transaction_date() == g2.generate_transaction_date()

    def test_same_seed_different_reference_now_diverges(self) -> None:
        g1 = self._make(7, DETERMINISTIC_ANCHOR)
        g2 = self._make(7, DETERMINISTIC_ANCHOR + timedelta(days=90))
        assert g1.generate_transaction_date() != g2.generate_transaction_date()

    def test_no_reference_now_still_works(self) -> None:
        g = self._make(7, None)
        result = g.generate_transaction_date()
        assert isinstance(result, datetime)


# ---------------------------------------------------------------------------
# OrderGenerator
# ---------------------------------------------------------------------------

class TestOrderGeneratorClockDeterminism:
    def _make(self, seed: int, reference_now: datetime | None) -> object:
        from datamimic_ce.domains.ecommerce.generators.order_generator import OrderGenerator

        return OrderGenerator(rng=random.Random(seed), reference_now=reference_now)

    def test_same_seed_same_reference_now_gives_identical_dates(self) -> None:
        g1 = self._make(99, DETERMINISTIC_ANCHOR)
        g2 = self._make(99, DETERMINISTIC_ANCHOR)
        assert g1.generate_order_date() == g2.generate_order_date()

    def test_same_seed_different_reference_now_diverges(self) -> None:
        g1 = self._make(99, DETERMINISTIC_ANCHOR)
        g2 = self._make(99, DETERMINISTIC_ANCHOR + timedelta(days=45))
        assert g1.generate_order_date() != g2.generate_order_date()

    def test_no_reference_now_still_works(self) -> None:
        g = self._make(99, None)
        result = g.generate_order_date()
        assert isinstance(result, datetime)


# ---------------------------------------------------------------------------
# MedicalDeviceGenerator — date helpers
# ---------------------------------------------------------------------------

class TestMedicalDeviceGeneratorClockDeterminism:
    def _make(self, seed: int, reference_now: datetime | None) -> object:
        from datamimic_ce.domains.healthcare.generators.medical_device_generator import MedicalDeviceGenerator

        return MedicalDeviceGenerator(rng=random.Random(seed), reference_now=reference_now)

    @pytest.mark.parametrize("method", [
        "generate_manufacture_date",
        "generate_expiration_date",
        "generate_last_maintenance_date",
        "generate_next_maintenance_date",
    ])
    def test_same_seed_same_reference_now_gives_identical_dates(self, method: str) -> None:
        g1 = self._make(11, DETERMINISTIC_ANCHOR)
        g2 = self._make(11, DETERMINISTIC_ANCHOR)
        assert getattr(g1, method)() == getattr(g2, method)()

    @pytest.mark.parametrize("method", [
        "generate_manufacture_date",
        "generate_last_maintenance_date",
    ])
    def test_same_seed_different_reference_now_diverges(self, method: str) -> None:
        g1 = self._make(11, DETERMINISTIC_ANCHOR)
        g2 = self._make(11, DETERMINISTIC_ANCHOR + timedelta(days=120))
        assert getattr(g1, method)() != getattr(g2, method)()

    def test_no_reference_now_still_works(self) -> None:
        g = self._make(11, None)
        result = g.generate_manufacture_date()
        assert isinstance(result, str)
        # must be parseable as YYYY-MM-DD
        datetime.strptime(result, "%Y-%m-%d")


# ---------------------------------------------------------------------------
# BirthdateGenerator
# ---------------------------------------------------------------------------

class TestBirthdateGeneratorClockDeterminism:
    def _make(self, seed: int, reference_now: datetime | None) -> object:
        from datamimic_ce.domains.common.literal_generators.birthdate_generator import BirthdateGenerator

        return BirthdateGenerator(rng=random.Random(seed), reference_now=reference_now)

    def test_same_seed_same_reference_now_gives_identical_birthdate(self) -> None:
        g1 = self._make(55, DETERMINISTIC_ANCHOR)
        g2 = self._make(55, DETERMINISTIC_ANCHOR)
        assert g1.generate() == g2.generate()

    def test_same_seed_different_reference_now_diverges(self) -> None:
        # A 30-year shift changes the age window noticeably
        anchor_b = datetime(2000, 1, 1, 12, 0, 0)
        g1 = self._make(55, DETERMINISTIC_ANCHOR)
        g2 = self._make(55, anchor_b)
        # The date ranges differ, so the generated dates should differ
        assert g1.generate() != g2.generate()

    def test_no_reference_now_still_works(self) -> None:
        g = self._make(55, None)
        result = g.generate()
        assert isinstance(result, datetime)

    def test_convert_birthdate_to_age_with_fixed_now(self) -> None:
        from datamimic_ce.domains.common.literal_generators.birthdate_generator import BirthdateGenerator

        birth = datetime(1990, 6, 15)
        ref = datetime(2025, 1, 1, 12, 0, 0)
        age = BirthdateGenerator.convert_birthdate_to_age(birth, reference_now=ref)
        assert age == 34
