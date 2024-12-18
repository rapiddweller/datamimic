# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path
from typing import Literal

from datamimic_ce.generators.generator import Generator
from datamimic_ce.utils.file_util import FileUtil


class GivenNameGenerator(Generator):
    """
    Generate random given name
    """

    def __init__(self, dataset: str, generated_count: int, gender: str | None = None):
        # check valid input dataset
        if len(dataset) != 2:
            raise ValueError(f"Invalid dataset: {dataset}")
        self._dataset = dataset
        self._gender = gender

        # Prepare file path
        prefix_path = Path(__file__).parent
        file_name_male = f"data/person/givenName_male_{dataset}.csv"
        file_name_female = f"data/person/givenName_female_{dataset}.csv"

        # Read file data
        if self._gender == "male":
            file_path = prefix_path.joinpath(file_name_male)
            data = self._select_records(file_path, generated_count)
            self._iter = iter(data)
        elif self._gender == "female":
            file_path = prefix_path.joinpath(file_name_female)
            data = self._select_records(file_path, generated_count)
            self._iter = iter(data)
        else:
            file_path_male = prefix_path.joinpath(file_name_male)
            data_male = self._select_records(file_path_male, generated_count)
            self._iter_male = iter(data_male)

            file_path_female = prefix_path.joinpath(file_name_female)
            data_female = self._select_records(file_path_female, generated_count)
            self._iter_female = iter(data_female)

    def _select_records(self, file_path, generated_count):
        try:
            values, wgt = FileUtil.read_mutil_column_wgt_file(file_path)
        except Exception as err:
            raise ValueError(f"Not support dataset: {self._dataset}") from err

        first_column = [row[0] for row in values]
        data = random.choices(first_column, wgt, k=generated_count)
        return iter(data)

    def generate(self) -> str:
        """
        Generate random given name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        if self._gender is None or self._gender == "other":
            return next(self._iter_male) if random.choice([True, False]) else next(self._iter_female)
        return next(self._iter)

    def generate_with_gender(self, gender: Literal["male", "female", "other"]):
        if gender == "male":
            return next(self._iter_male)
        elif gender == "female":
            return next(self._iter_female)
        else:
            return next(self._iter_male) if random.choice([True, False]) else next(self._iter_female)
