# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.generators.generator import Generator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class NobilityTitleGenerator(Generator):
    """
    Generate random nobility title
    """

    def __init__(self, dataset: str | None = None, gender: str | None = None, noble_quota: float | None = None):
        self._gender = gender
        self._noble_quota = noble_quota if noble_quota is not None else 0.001

        sp_dataset = ("de", "en", "es", "fr", "it")
        if dataset is not None:
            dataset = None if dataset.lower() not in sp_dataset else dataset.lower()

        # Prepare file path
        prefix_path = Path(__file__).parent
        if dataset:
            file_name_male = f"data/person/nobTitle_male_{dataset}.csv"
            file_name_female = f"data/person/nobTitle_female_{dataset}.csv"
        else:
            file_name_male = "data/person/nobTitle_male.csv"
            file_name_female = "data/person/nobTitle_female.csv"

        male_file_path = prefix_path.joinpath(file_name_male)
        female_file_path = prefix_path.joinpath(file_name_female)

        file_content_storage = FileContentStorage()
        self._male_values, self._male_weights = file_content_storage.load_file_with_custom_func(
            file_path_str=str(male_file_path),
            read_func=lambda: FileUtil.read_wgt_file(file_path=male_file_path),
        )

        self._female_values, self._female_weights = file_content_storage.load_file_with_custom_func(
            file_path_str=str(female_file_path),
            read_func=lambda: FileUtil.read_wgt_file(file_path=female_file_path),
        )

    def generate(self) -> str | None:
        """
        Generate random nobility title
            Returns:
                Optional[str]: Returns a string if successful, otherwise returns None.
        """
        if self._gender in ["male", "female", "other"]:
            return self.generate_with_gender(self._gender)
        else:
            return ""

    def generate_with_gender(self, gender: str):
        """
        Generate random nobility title
            Returns:
                Optional[str]: Returns a string if successful, otherwise returns None.
        """
        if random.random() < self._noble_quota:
            if gender == "male":
                return random.choices(self._male_values, self._male_weights, k=1)[0] if self._male_values else None
            elif gender == "female":
                return (
                    random.choices(self._female_values, self._female_weights, k=1)[0] if self._female_values else None
                )
            else:
                """"""
        else:
            return ""
