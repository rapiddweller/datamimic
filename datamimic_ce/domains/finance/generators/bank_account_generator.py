# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
import random
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.finance.generators.bank_generator import BankGenerator
from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage


class BankAccountGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str = "US"):
        super().__init__(dataset=dataset)
        self._dataset = dataset
        self._bank_generator = BankGenerator(dataset=dataset)
        self._account_number_generator = DataFakerGenerator(locale=dataset, provider="bban")

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
        cache_key = f"bank_account_types_{self.dataset}"
        if cache_key not in self._LOADED_DATA_CACHE:
            file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "finance" / "bank" / f"account_types_{self.dataset}.csv"
            account_types_data = FileContentStorage.load_file_with_custom_func(str(file_path), lambda: FileUtil.read_csv_file(file_path))
            self._LOADED_DATA_CACHE[cache_key] = account_types_data
        
        return random.choices(self._LOADED_DATA_CACHE[cache_key], weights=[item[1] for item in self._LOADED_DATA_CACHE[cache_key]], k=1)[0][0]

