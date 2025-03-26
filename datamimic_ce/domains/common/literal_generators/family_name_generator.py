# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.utils.file_util import FileUtil


class FamilyNameGenerator(BaseLiteralGenerator):
    """
    Generate random family name
    """

    def __init__(self, dataset: str):
        self._dataset = dataset or "US"

        try:
            file_path = Path(__file__).parent.parent.parent.parent.joinpath(
                f"domain_data/common/person/familyName_{self._dataset}.csv"
            )
            values, wgt = FileUtil.read_mutil_column_wgt_file(
                file_path,
            )

            first_column = [row[0] for row in values]
            self._loaded_data = first_column, wgt
        except Exception as err:
            raise ValueError(f"Not support dataset: {dataset}: {err}") from err

    def generate(self) -> str:
        """
        Generate random family name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        return random.choices(self._loaded_data[0], self._loaded_data[1], k=1)[0]
