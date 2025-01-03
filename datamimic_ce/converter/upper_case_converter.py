# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.converter.converter import Converter


class UpperCaseConverter(Converter):
    """
    Convert string data to upper case
    """

    def convert(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"Converter UpperCase expect datatype 'string', "
                f"but got value {value} with invalid datatype {type(value)}"
            )
        return value.upper()
