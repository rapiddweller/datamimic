# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.generators.generator import Generator
from datamimic_ce.utils.file_util import FileUtil


class FamilyNameGenerator(Generator):
    """
    Generate random family name
    """

    def __init__(self, dataset: str, generated_count: int):
        # check valid input dataset
        if len(dataset) != 2:
            raise ValueError(f"Invalid dataset: {dataset}")

        try:
            file_path = Path(__file__).parent.joinpath(f"data/person/familyName_{dataset}.csv")
            values, wgt = FileUtil.read_mutil_column_wgt_file(
                file_path,
            )
        except Exception as err:
            raise ValueError(f"Not support dataset: {dataset}") from err

        first_column = [row[0] for row in values]
        data = random.choices(first_column, wgt, k=generated_count)
        self._iter = iter(data)

    def generate(self) -> str:
        """
        Generate random family name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        return next(self._iter)
