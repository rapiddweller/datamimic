# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import DatasetAwareDomainGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class FamilyNameGenerator(DatasetAwareDomainGenerator):
    """
    Generate random family name
    """

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        super().__init__(dataset=dataset, rng=rng)

        try:
            file_path = dataset_path("common", "person", f"familyName_{self._dataset}.csv", start=Path(__file__))
            values, wgt = FileUtil.read_mutil_column_wgt_file(file_path)
            first_column = [row[0] for row in values]
            self._loaded_data = first_column, wgt
        except Exception as err:
            raise ValueError(f"Not support dataset: {self._dataset}: {err}") from err

    def generate(self) -> str:
        """
        Generate random family name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        return self._rng.choices(self._loaded_data[0], self._loaded_data[1], k=1)[0]
