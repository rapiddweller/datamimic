# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

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
