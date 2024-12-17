# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datetime import datetime

from datamimic_ce.converter.converter import Converter


class Timestamp2DateConverter(Converter):
    """
    Convert timestamp data (int or float) to datetime
    """

    def convert(self, value: int | float) -> datetime:
        if not isinstance(value, int | float):
            raise ValueError(
                f"Converter Timestamp2Date expect datatype 'int' or 'float', "
                f"but got value {value} with invalid datatype {type(value)}"
            )

        return datetime.fromtimestamp(value)
