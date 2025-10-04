# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class StreetNameGenerator(BaseLiteralGenerator):
    """
    Generate random street name
    """

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        dataset = dataset or "US"
        street_code = dataset.upper()[:2]

        # Prepare file path
        file_path = dataset_path("common", "street", f"street_{street_code}.csv", start=Path(__file__))

        # Load file data
        self._values, self._wgt = FileUtil.read_wgt_file(file_path)
        self._rng: random.Random = rng or random.Random()

    def generate(self) -> str:
        """
        Generate random street name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        return self._rng.choices(self._values, self._wgt, k=1)[0]
