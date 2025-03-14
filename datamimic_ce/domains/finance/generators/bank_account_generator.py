# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
import random
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class BankAccountGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str = "US"):
        self._dataset = dataset
        self._bank_generator = BankGenerator(dataset=dataset)
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

    def get_bank_account_types(self) -> dict:
        file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "finance" / "bank" / f"account_types_{self.dataset}.csv"
        account_types_data = FileContentStorage.load_file_with_custom_func(str(file_path), lambda: FileUtil.read_csv_file(file_path))
        return random.choices(account_types_data, weights=[item[1] for item in account_types_data], k=1)[0][0]


