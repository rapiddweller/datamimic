# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
import random
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil

class CreditCardGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str = "US"):
        super().__init__(dataset=dataset)
        self._dataset = dataset
        
    def generate_card_type(self) -> str:
        cache_key = f"card_types_{self.dataset}"
        if cache_key not in self._LOADED_DATA_CACHE:
            file_path = Path(__file__).parent.parent.parent.parent / "domain_data" / "finance" / "credit_card" / f"card_types_{self.dataset}.csv"
            card_types_data = FileContentStorage.load_file_with_custom_func(str(file_path), lambda: FileUtil.read_csv_file(file_path))
            self._LOADED_DATA_CACHE[cache_key] = card_types_data
        
        return random.choice(self._LOADED_DATA_CACHE[cache_key])
    