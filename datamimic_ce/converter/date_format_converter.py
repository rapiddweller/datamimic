# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

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
