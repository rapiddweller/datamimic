# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from typing import Any

from datamimic_ce.converter.converter import Converter


class AppendConverter(Converter):
    """ """

    def __init__(self, append_char: str):
        if not isinstance(append_char, str):
            raise ValueError(
                f"Converter Append expect a string as input for but got value {append_char} "
                f"with invalid datatype {type(append_char)}"
            )
        self._append_char = append_char

    def convert(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"Converter Append expect datatype 'string', but got value {value} with invalid datatype {type(value)}"
            )
        else:
            return value + self._append_char
