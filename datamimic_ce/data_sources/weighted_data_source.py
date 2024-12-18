# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.generators.generator import Generator
from datamimic_ce.utils.file_util import FileUtil


class WeightedDataSource(Generator):
    """
    Generate data from weighted data source (.wgt.csv)
    """

    def __init__(self, file_path: Path, separator: str):
        self._file_path = file_path
        # read_csv and replace empty value as None instead of the default nan.
        # nan when convert into Json cause invalid json format where None become null which is still valid.
        self._df = FileUtil.read_weight_csv(file_path, separator)

    def generate(self):
        """
        Get a random choice from dataframe with weight
        """
        try:
            return random.choices(self._df[0], weights=self._df[1], k=1)[0]
        except Exception as err:
            raise ValueError(
                f"Cannot get data from csv file '{self._file_path}', please check file path or separator again: {err}"
            ) from err
