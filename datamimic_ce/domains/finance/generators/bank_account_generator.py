# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import ClockAnchoredDomainGenerator
from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.domains.shared.datasets.loader import pick_one_weighted, read_csv_rows
from datamimic_ce.domains.shared.literal_generators.primitives.data_faker_generator import DataFakerGenerator

_DIGITS = "0123456789"
_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# ISO 13616 character classes: n = digits, a = upper-case letters, c = alphanumeric.
_CLASS_CHARS = {"n": _DIGITS, "a": _UPPER, "c": _UPPER + _DIGITS}
_IBAN_PREFIX_LENGTH = 4

# ISO 13616-1:2020 BBAN structure per country as (class, length) segments, the same table as EE.
# A country that is not listed has no IBAN here. Belgium and Spain are left out on purpose: their BBAN
# holds national check digits that this table does not compute.
_BBAN_SPECS: dict[str, tuple[tuple[str, int], ...]] = {
    "AT": (("n", 16),),
    "CH": (("n", 5), ("c", 12)),
    "DE": (("n", 18),),
    "FR": (("n", 10), ("c", 11), ("n", 2)),
    "GB": (("a", 4), ("n", 6), ("n", 8)),
    "IT": (("a", 1), ("n", 10), ("c", 12)),
    "NL": (("a", 4), ("n", 10)),
    "PT": (("n", 21),),
}


def _mod97(iban: str) -> int:
    """Return the ISO 7064 mod 97 remainder of an IBAN string; a letter A to Z counts 10 to 35."""
    total = 0
    for char in iban:
        total = (total * 10 + ord(char) - 48) % 97 if char.isdigit() else (total * 100 + ord(char) - 55) % 97
    return total


class BankAccountGenerator(ClockAnchoredDomainGenerator):
    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
        reference_now: datetime.datetime | None = None,
    ):
        super().__init__(dataset=dataset, rng=rng, reference_now=reference_now)
        self._bank_generator = BankGenerator(
            dataset=self._dataset,
            rng=self._derive_rng(),
        )
        # Seed Faker with a derived RNG so account numbers replay under rngSeed-configured descriptors.
        self._account_number_generator = DataFakerGenerator(
            "bban",
            rng=self._derive_rng(),
        )

    @property
    def bank_generator(self) -> BankGenerator:
        return self._bank_generator

    @property
    def account_number_generator(self) -> DataFakerGenerator:
        return self._account_number_generator

    #  Centralize date generation to keep models pure and RNG deterministic
    def generate_created_date(self) -> datetime.datetime:
        from datamimic_ce.domains.shared.literal_generators.temporal.datetime_generator import DateTimeGenerator

        now = self._reference_now
        min_dt = (now - datetime.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = now.strftime("%Y-%m-%d %H:%M:%S")
        dt = DateTimeGenerator(
            min=min_dt,
            max=max_dt,
            random=True,
            rng=self._derive_rng(),
        ).generate()
        assert isinstance(dt, datetime.datetime)
        return dt

    def generate_last_transaction_date(self, created_date: datetime.datetime) -> datetime.datetime:
        from datamimic_ce.domains.shared.literal_generators.temporal.datetime_generator import DateTimeGenerator

        now = self._reference_now
        min_dt = created_date.strftime("%Y-%m-%d %H:%M:%S")
        max_dt = now.strftime("%Y-%m-%d %H:%M:%S")
        dt = DateTimeGenerator(
            min=min_dt,
            max=max_dt,
            random=True,
            rng=self._derive_rng(),
        ).generate()
        assert isinstance(dt, datetime.datetime)
        return dt

    def get_bank_account_types(self) -> str:
        file_path = dataset_path("finance", f"account_types_{self.dataset}.csv", start=Path(__file__))
        account_types_data = read_csv_rows(file_path)[1:]
        values = [row[0] for row in account_types_data]
        weights = [float(item[1]) for item in account_types_data]
        choice = pick_one_weighted(self._rng, values, weights)
        return choice

    def generate_balance(self) -> float:
        return self.rng.uniform(0, 1000000)

    def get_currency(self) -> str:
        file_path = dataset_path("ecommerce", f"currencies_{self.dataset}.csv", start=Path(__file__))
        raw_rows = read_csv_rows(file_path)
        if len(raw_rows) <= 1:
            raise ValueError(f"{file_path} has no data rows")
        header = raw_rows[0]
        rows = raw_rows[1:]
        header_map = {str(col).strip().lower(): idx for idx, col in enumerate(header)}
        if "code" not in header_map or "weight" not in header_map:
            raise ValueError(f"{file_path} is missing 'code'/'weight' columns (header: {list(header)})")
        code_idx = header_map["code"]
        weight_idx = header_map["weight"]
        weights = [float(row[weight_idx]) for row in rows]
        codes = [row[code_idx] for row in rows]
        choice = pick_one_weighted(self._rng, codes, weights)
        return choice

    def generate_iban(self) -> str | None:
        """Return an IBAN of the dataset's country, or None for a country without an IBAN scheme."""
        country = self.dataset[:2].upper()
        spec = _BBAN_SPECS.get(country)
        if spec is None:
            return None
        bban = "".join(self.rng.choice(_CLASS_CHARS[kind]) for kind, length in spec for _ in range(length))
        check = 98 - _mod97(f"{bban}{country}00")
        return f"{country}{check:02d}{bban}"
