# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random

from datamimic_ce.generators.generator import Generator


class GenderGenerator(Generator):
    """
    Purpose: generate Person Gender (MALE or FEMALE) based on female quota.

    Extends: Generator (Abstract Class).

    Attributes:
        female_quota (float): female quota to generate FEMALE gender.
    """

    def __init__(self, female_quota: float | None = None, other_gender_quota: float | None = None):
        """
        Constructor for GenderGenerator with default quota of female/male/other are 0.49/0.49/0.02
        (if argument is not passed in constructor).
        if any argument is passed in constructor, that argument has priority.
        if all arguments are passed in constructor, female_quota has priority, then other_gender_quota.

        Parameters:
            female_quota (float - default = 0.49 - max = 1): female quota to generate FEMALE gender
            other_gender_quota (float - default = 0.02 - max = 1):  non-gender quota to generate OTHER gender

        Returns:
            GenderGenerator: new instance
        """
        female_quota, male_quota, other_gender_quota = self._calculate_gender_rate(female_quota, other_gender_quota)
        self._wgt = [female_quota, male_quota, other_gender_quota]
        self._values = ["female", "male", "other"]

    def generate(self) -> str:
        """
        Generate the string of gender: male, female or other based on quotas.

        Returns:
            str: generated string gender
        """
        return random.choices(self._values, weights=self._wgt, k=1)[0]

    @staticmethod
    def _calculate_gender_rate(female_quota, other_gender_quota):
        # quota must in range 0->1
        female_quota = min(max(female_quota, 0), 1) if female_quota is not None else None
        other_gender_quota = min(max(other_gender_quota, 0), 1) if other_gender_quota is not None else None

        # Handling None values
        if female_quota is None and other_gender_quota is None:
            female_quota = 0.49
            other_gender_quota = 0.02
        elif female_quota is None:
            female_quota = (1 - other_gender_quota) / 2
        elif other_gender_quota is None:
            other_gender_quota = 0.2

        # Adjust so that the sum does not exceed 1
        if female_quota + other_gender_quota > 1:
            other_gender_quota = 1 - female_quota

        # Calculate male_quota
        male_quota = 1 - female_quota - other_gender_quota

        return female_quota, male_quota, other_gender_quota
