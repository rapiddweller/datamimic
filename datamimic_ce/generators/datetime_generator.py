# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import random
from datetime import datetime, timedelta

from datamimic_ce.generators.generator import Generator


class DateTimeGenerator(Generator):
    # Define mode of DateGenerator
    _CUSTOM_DATETIME_MODE = "custom"
    _RANDOM_DATETIME_MODE = "random"
    _CURRENT_DATETIME_MODE = "current"

    def __init__(
        self,
        min: str = None,
        max: str = None,
        value: str = None,
        random: bool = False,
        input_format: str = None,
    ):
        input_format = input_format if input_format else "%Y-%m-%d %H:%M:%S"
        # Handle custom (fixed) datetype value
        if value:
            self._result = datetime.strptime(value, input_format)
            self._mode = self._CUSTOM_DATETIME_MODE
        # Handle random datetime
        elif random or min or max:
            self._time_difference = timedelta(365.25 * 50)
            if min and max:
                self._start_date = datetime.strptime(min, input_format)
                self._time_difference = datetime.strptime(max, input_format) - self._start_date
                if self._time_difference < timedelta(0):
                    raise ValueError("max_datetime must be greater than min_datetime")
            elif min:
                self._start_date = datetime.strptime(min, input_format)
            elif max:
                self._start_date = datetime.strptime(max, input_format) - self._time_difference
            else:
                self._start_date = datetime.strptime("1970-01-01 00:00:00", input_format)

            self._mode = self._RANDOM_DATETIME_MODE
        # Handle datetime.now()
        else:
            self._result = datetime.now()
            self._mode = self._CURRENT_DATETIME_MODE

    def generate(self) -> datetime | str:
        if self._mode == self._RANDOM_DATETIME_MODE:
            random_seconds = random.randint(0, int(self._time_difference.total_seconds()))
            result = self._start_date + timedelta(seconds=random_seconds)
        else:
            result = self._result
        return result
