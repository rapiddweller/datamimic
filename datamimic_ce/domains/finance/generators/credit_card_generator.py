# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.person_generator import PersonGenerator
from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator
from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.utils.file_util import FileUtil


class CreditCardGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None):
        self._dataset = dataset or "US"
        self._person_generator = PersonGenerator()
        self._date_generator = DateTimeGenerator(random=True)
        self._bank_account_generator = BankAccountGenerator(dataset=self._dataset)

    @property
    def person_generator(self) -> PersonGenerator:
        return self._person_generator

    @property
    def date_generator(self) -> DateTimeGenerator:
        return self._date_generator

    @property
    def bank_account_generator(self) -> BankAccountGenerator:
        return self._bank_account_generator

    def generate_card_type(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data"
            / "finance"
            / "credit_card"
            / f"card_types_{self._dataset}.csv"
        )
        card_types_data = FileUtil.read_csv_to_list_of_tuples_without_header(file_path)[1:]
        return random.choices(card_types_data, weights=[float(item[4]) for item in card_types_data], k=1)[0][0]
