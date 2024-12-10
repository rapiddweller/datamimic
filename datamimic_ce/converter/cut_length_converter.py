# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.converter.converter import Converter


class CutLengthConverter(Converter):
    """
    A converter to remove a specified number of characters from the beginning of a string.
    Parameters:
        length_to_cut (int): The number of characters to cut from the beginning of the string.
    """

    def __init__(self, length_to_cut: int):
        if not isinstance(length_to_cut, int):
            raise ValueError(
                f"Converter CutLength expect an interger as input for how many character to cut "
                f"'int', but got value {length_to_cut} with invalid datatype {type(length_to_cut)}"
            )
        self._length_to_cut = length_to_cut

    def convert(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"Converter CutLength expect datatype 'string', but got value {value} "
                f"with invalid datatype {type(value)}"
            )
        else:
            return value[: self._length_to_cut]
