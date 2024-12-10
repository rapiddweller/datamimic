# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.converter.converter import Converter


class MiddleMaskConverter(Converter):
    """
    A converter to mask characters in the middle of a string, leaving specified characters unmasked.

    Parameters:
        start_mask_index (int): The index of the first character to mask from the beginning (0-based).
        end_mask_offset (int): The number of characters to mask from the end of the string.
        mask_char (str, optional): The character used for masking. Default is "*".

    Example: MiddleMask(2,3) for '0123456789' output: '01*****789'
    """

    def __init__(self, start_mask_index: int, end_mask_offset: int, mask_char: str = "*"):
        if len(mask_char) != 1:
            raise ValueError("Mask character can only be a single character")
        self._start_mask_index = start_mask_index
        self._end_mask_offset = end_mask_offset
        self._mask_char = mask_char

    def convert(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"MiddleMaskConverter expects data type 'string', but got value {value} "
                f"with an invalid datatype {type(value)}"
            )

        if (
            self._start_mask_index >= len(value)
            or self._end_mask_offset >= len(value)
            or self._start_mask_index > self._end_mask_offset
        ):
            return value  # Nothing to mask, return the original value.

        end_mask_index = len(value) - self._end_mask_offset
        masked_chars = value[self._start_mask_index : end_mask_index]
        masked_string = value[: self._start_mask_index] + self._mask_char * len(masked_chars) + value[end_mask_index:]

        return masked_string
