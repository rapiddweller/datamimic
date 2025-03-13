# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class BankGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str = "US"):
        self._dataset = dataset

    def generate_bank_data(self) -> dict:
        cache_key = f"bank_name_{self._dataset}"
        if cache_key not in self._LOADED_DATA_CACHE:
            file_path = Path(
                __file__).parent.parent.parent / "domain_data" / "finance" / "bank" / f"banks_{self._dataset}.csv"
            self._LOADED_DATA_CACHE[cache_key] = FileContentStorage.load_file_with_custom_func(cache_key=str(file_path),
                                                                                               read_func=lambda: FileUtil.read_csv_to_list_of_tuples_without_header(
                                                                                                   file_path,
                                                                                                   delimiter=","))
        loaded_data = self._LOADED_DATA_CACHE[cache_key]

        bank_data = random.choices(loaded_data, weights=[row[3] for row in loaded_data])[0]

        return {
            "name": bank_data[0],
            "swift_code": bank_data[1],
            "routing_number": bank_data[2],
            "bank_code": bank_data[3]
        }
