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


class GivenNameGenerator(BaseLiteralGenerator):
    """
    Generate random given name
    """

    def __init__(self, dataset: str | None = None, gender: str | None = None, rng: random.Random | None = None):
        self._dataset = dataset or "US"
        self._gender = gender
        self._rng: random.Random = rng or random.Random()
        self._last_given: str | None = None

        # Prepare file path
        file_name_male = f"givenName_male_{self._dataset}.csv"
        file_name_female = f"givenName_female_{self._dataset}.csv"

        # Read file data
        if self._gender == "male":
            file_path = dataset_path("common", "person", file_name_male, start=Path(__file__))
            self._dataset = self._select_records(file_path)
        elif self._gender == "female":
            file_path = dataset_path("common", "person", file_name_female, start=Path(__file__))
            self._dataset = self._select_records(file_path)
        else:
            file_path_male = dataset_path("common", "person", file_name_male, start=Path(__file__))
            self._dataset_male = self._select_records(file_path_male)
            file_path_female = dataset_path("common", "person", file_name_female, start=Path(__file__))
            self._dataset_female = self._select_records(file_path_female)

    def _select_records(self, file_path):
        try:
            values, wgt = FileUtil.read_mutil_column_wgt_file(file_path)
            first_column = [row[0] for row in values]
            return first_column, wgt
        except Exception as err:
            raise ValueError(f"Not support dataset: {self._dataset}: {err}") from err

    def generate(self) -> str:
        """
        Generate random given name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        return self.generate_with_gender(self._gender)

    def generate_with_gender(self, gender: str | None):
        """
        Generate random given name with gender
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        if gender == "male":
            selected_dataset = self._dataset_male
        elif gender == "female":
            selected_dataset = self._dataset_female
        elif self._gender == "other" or self._gender is None:
            selected_dataset = self._dataset_male if self._rng.choice([True, False]) else self._dataset_female
        else:
            raise ValueError(f"Invalid gender: {gender}")
        # Avoid immediate repetition when possible
        values, weights = selected_dataset[0], selected_dataset[1]
        if self._last_given in values and len(values) > 1:
            pool = [(v, w) for v, w in zip(values, weights, strict=False) if v != self._last_given]
            vals, wgts = zip(*pool, strict=False)
            choice = self._rng.choices(list(vals), weights=list(wgts), k=1)[0]
        else:
            choice = self._rng.choices(values, weights, k=1)[0]
        self._last_given = choice
        return choice
