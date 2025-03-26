# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


def generate_random_float_2dp(start, end):
    import random

    """
    Generate a random float within a given range with a maximum of two decimal places.

    Parameters:
    start (float): The start of the range.
    end (float): The end of the range.

    Returns:
    float: A random float within the specified range, rounded to two decimal places.
    """
    if start > end:
        raise ValueError("Start value must be less than or equal to end value.")

    return round(random.uniform(start, end), 2)
