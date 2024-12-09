# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/



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
