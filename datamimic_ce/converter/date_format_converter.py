# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datetime import datetime

from datamimic_ce.converter.converter import Converter


class DateFormatConverter(Converter):
    """
    Convert string data to lower case
    """

    def __init__(self, format_str: str):
        self._format = format_str

    def convert(self, value: datetime) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError(
                f"Converter DateFormat expect datatype 'datetime', but got value {value} "
                f"with invalid datatype {type(value)}"
            )
        formatted_datetime = value.strftime(self._format)
        return datetime.strptime(formatted_datetime, self._format)
