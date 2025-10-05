# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
from pathlib import Path

from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class BankAccountGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        self._dataset = (dataset or "US").upper()  #  match dataset-specific CSV suffixes
        self._rng: random.Random = rng or random.Random()
        self._bank_generator = BankGenerator(dataset=self._dataset, rng=self._rng)
        # Seed Faker with a derived RNG so account numbers replay under rngSeed-configured descriptors.
        self._account_number_generator = DataFakerGenerator(
            "bban",
            rng=self._derive_rng(),
        )
        self._last_account_type: str | None = None
        self._last_currency: str | None = None

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def bank_generator(self) -> BankGenerator:
        return self._bank_generator

    @property
    def account_number_generator(self) -> DataFakerGenerator:
        return self._account_number_generator

    @property
    def rng(self) -> random.Random:
        return self._rng

    #  Centralize date generation to keep models pure and RNG deterministic
    def generate_created_date(self) -> datetime.datetime:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
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
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
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

    def _derive_rng(self) -> random.Random:
        # Fork deterministic child RNGs so seeded generators remain reproducible without sharing state globally.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    def get_bank_account_types(self) -> str:
        file_path = dataset_path("finance", f"account_types_{self.dataset}.csv", start=Path(__file__))
        account_types_data = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)[1:]
        weights = [float(item[1]) for item in account_types_data]
        # Avoid immediate repetition
        if self._last_account_type is not None and len(account_types_data) > 1:
            pool = [
                (row, w)
                for row, w in zip(account_types_data, weights, strict=False)
                if row[0] != self._last_account_type
            ]
            rows, wgts = zip(*pool, strict=False)
            choice = self._rng.choices(list(rows), weights=list(wgts), k=1)[0][0]
        else:
            choice = self._rng.choices(account_types_data, weights=weights, k=1)[0][0]
        self._last_account_type = choice
        return choice

    def get_currency(self) -> str:
        file_path = dataset_path("ecommerce", f"currencies_{self.dataset}.csv", start=Path(__file__))
        raw_rows = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)
        if not raw_rows or len(raw_rows) == 1:
            return "USD"
        header = raw_rows[0]
        rows = raw_rows[1:]
        header_map = {str(col).strip().lower(): idx for idx, col in enumerate(header)}
        weight_idx = header_map.get("weight")
        code_idx = header_map.get("code", 0)
        # accommodate datasets that only expose code+weight without extra columns.
        if weight_idx is None:
            weight_idx = len(header) - 1 if len(header) > 1 else None
        weights = [1.0 for _ in rows] if weight_idx is None else [float(row[weight_idx]) for row in rows]
        codes = [row[code_idx] for row in rows]
        # Avoid immediate repetition
        if self._last_currency is not None and len(codes) > 1:
            pool = [(code, w) for code, w in zip(codes, weights, strict=False) if code != self._last_currency]
            if pool:
                codes_filtered, weights_filtered = zip(*pool, strict=False)
                codes = list(codes_filtered)
                weights = list(weights_filtered)
        choice = self._rng.choices(list(codes), weights=list(weights), k=1)[0]
        self._last_currency = choice
        return choice
