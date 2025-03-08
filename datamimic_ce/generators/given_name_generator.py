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

    def __init__(self, dataset: str, gender: str | None = None):
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
            self._dataset = self._select_records(file_path)
        elif self._gender == "female":
            file_path = prefix_path.joinpath(file_name_female)
            self._dataset = self._select_records(file_path)
        else:
            file_path_male = prefix_path.joinpath(file_name_male)
            self._dataset_male = self._select_records(file_path_male)

            file_path_female = prefix_path.joinpath(file_name_female)
            self._dataset_female = self._select_records(file_path_female)

    def _select_records(self, file_path):
        try:
            values, wgt = FileUtil.read_mutil_column_wgt_file(file_path)

            first_column = [row[0] for row in values]
            return first_column, wgt
        
        except Exception as err:
            raise ValueError(f"Not support dataset: {self._dataset}") from err

    def generate(self) -> str:
        """
        Generate random given name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        return self.generate_with_gender(self._gender)

    def generate_with_gender(self, gender: Literal["male", "female", "other"]):
        """
        Generate random given name with gender
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        if gender == "male":
            selected_dataset = self._dataset_male
        elif gender == "female":
            selected_dataset = self._dataset_female
        else:
            selected_dataset = self._dataset_male if random.choice([True, False]) else self._dataset_female
        return random.choices(selected_dataset[0], selected_dataset[1], k=1)[0]
