# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.utils.file_util import FileUtil


class BankAccountGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None):
        self._dataset = dataset or "US"
        self._bank_generator = BankGenerator(dataset=self._dataset)
        self._account_number_generator = DataFakerGenerator("bban")

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def bank_generator(self) -> BankGenerator:
        return self._bank_generator

    @property
    def account_number_generator(self) -> DataFakerGenerator:
        return self._account_number_generator

    def get_bank_account_types(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent / "domain_data" / "finance" / f"account_types_{self.dataset}.csv"
        )
        account_types_data = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)[1:]
        return random.choices(account_types_data, weights=[float(item[1]) for item in account_types_data], k=1)[0][0]

    def get_currency(self) -> str:
        file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "ecommerce" / "currencies.csv"
        currency_data = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)[1:]
        return random.choices(currency_data, weights=[float(item[2]) for item in currency_data], k=1)[0][0]
