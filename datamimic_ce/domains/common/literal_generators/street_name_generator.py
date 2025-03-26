# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class StreetNameGenerator(BaseLiteralGenerator):
    """
    Generate random street name
    """

    def __init__(self, dataset: str | None = None):
        dataset = dataset or "US"
        street_code = dataset.upper()[:2]

        # Prepare file path
        prefix_path = Path(__file__).parent.parent.parent.parent
        file_name = f"domain_data/common/street/street_{street_code}.csv"
        file_path = prefix_path.joinpath(file_name)

        # Load file data
        try:
            self._values, self._wgt = FileUtil.read_wgt_file(file_path)
        except FileNotFoundError as e:
            logger.error(f"Street name data not found for dataset '{dataset}'")
            raise FileNotFoundError(f"Street name data not found for dataset '{dataset}': {e}") from e

    def generate(self) -> str:
        """
        Generate random street name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        return random.choices(self._values, self._wgt, k=1)[0]
