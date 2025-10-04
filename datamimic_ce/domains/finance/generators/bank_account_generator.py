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
        self._account_number_generator = DataFakerGenerator("bban")
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
        dt = DateTimeGenerator(min=min_dt, max=max_dt, random=True).generate()
        assert isinstance(dt, datetime.datetime)
        return dt

    def generate_last_transaction_date(self, created_date: datetime.datetime) -> datetime.datetime:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = datetime.datetime.now()
        min_dt = created_date.strftime("%Y-%m-%d %H:%M:%S")
        max_dt = now.strftime("%Y-%m-%d %H:%M:%S")
        dt = DateTimeGenerator(min=min_dt, max=max_dt, random=True).generate()
        assert isinstance(dt, datetime.datetime)
        return dt

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
        currency_data = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)[1:]
        weights = [float(item[2]) for item in currency_data]
        # Avoid immediate repetition
        if self._last_currency is not None and len(currency_data) > 1:
            pool = [(row, w) for row, w in zip(currency_data, weights, strict=False) if row[0] != self._last_currency]
            rows, wgts = zip(*pool, strict=False)
            choice = self._rng.choices(list(rows), weights=list(wgts), k=1)[0][0]
        else:
            choice = self._rng.choices(currency_data, weights=weights, k=1)[0][0]
        self._last_currency = choice
        return choice
