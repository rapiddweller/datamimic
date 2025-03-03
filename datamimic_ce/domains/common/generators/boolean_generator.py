# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random


class BooleanGenerator:
    """
    Purpose: generate a random boolean value (True or False).

    Use case (config):
        - Generate a random boolean with equal probability.
        Example: boolean_generator = BooleanGenerator()
        - Generate a random boolean with custom probability for True.
        Example: boolean_generator = BooleanGenerator(prob_true=0.7)

    Attributes:
        prob_true (float): probability of generating a True value (default is 0.5).
    """

    def __init__(self, prob_true: float = 0.5) -> None:
        """
        Parameters:
            prob_true (float): probability of generating a True value (default is 0.5).

        Throws:
            ValueError: Probability prob_true of BooleanGenerator must be in [0.0, 1.0] range,
            but got invalid value {prob_true}.
        """
        if not (0.0 <= prob_true <= 1.0):
            raise ValueError(
                f"Probability prob_true of BooleanGenerator must be in [0.0, 1.0] range, "
                f"but got invalid value {prob_true}."
            )
        self.prob_true = prob_true

    def generate(self) -> bool:
        """
        Generate a random boolean based on probability of being True.

        Returns:
            bool: generated boolean value
        """
        return random.random() < self.prob_true
