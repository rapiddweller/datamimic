# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datetime import datetime

from datamimic_ce.converter.converter import Converter


class Date2TimestampConverter(Converter):
    """
    Convert datetime data to timestamp (float)
    """

    def convert(self, value: datetime) -> int:
        if not isinstance(value, datetime):
            raise ValueError(
                f"Converter Date2Timestamp expect datatype 'datetime', "
                f"but got value {value} with invalid datatype {type(value)}"
            )

        return int(value.timestamp())
