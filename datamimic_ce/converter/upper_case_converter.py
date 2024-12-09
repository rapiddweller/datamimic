# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from typing import Any

from datamimic_ce.converter.converter import Converter


class UpperCaseConverter(Converter):
    """
    Convert string data to upper case
    """

    def convert(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"Converter UpperCase expect datatype 'string', but got value {value} with invalid datatype {type(value)}"
            )
        return value.upper()
