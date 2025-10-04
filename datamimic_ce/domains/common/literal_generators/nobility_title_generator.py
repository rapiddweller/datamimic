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


class NobilityTitleGenerator(BaseLiteralGenerator):
    """
    Generate random nobility title
    """

    def __init__(
        self,
        dataset: str | None = None,
        gender: str | None = None,
        noble_quota: float | None = None,
        rng: random.Random | None = None,
    ):
        self._gender = gender
        self._noble_quota = noble_quota if noble_quota is not None else 0.001
        self._rng: random.Random = rng or random.Random()

        allowed = {"DE", "GB", "ES", "FR", "IT", "US"}
        normalized_dataset = (dataset or "US").upper()
        if normalized_dataset not in allowed:
            normalized_dataset = "US"  #  default to US titles when dataset-specific data is unavailable

        male_file_path = dataset_path(
            "common", "person", f"nobTitle_male_{normalized_dataset}.csv", start=Path(__file__)
        )
        female_file_path = dataset_path(
            "common", "person", f"nobTitle_female_{normalized_dataset}.csv", start=Path(__file__)
        )

        self._male_values, self._male_weights = FileUtil.read_wgt_file(file_path=male_file_path)
        self._female_values, self._female_weights = FileUtil.read_wgt_file(file_path=female_file_path)

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
        if self._rng.random() < self._noble_quota:
            if gender == "male":
                return self._male_values and self._rng.choices(self._male_values, self._male_weights, k=1)[0] or None
            elif gender == "female":
                return (
                    self._female_values and self._rng.choices(self._female_values, self._female_weights, k=1)[0] or None
                )
            else:
                """"""
        else:
            return ""
