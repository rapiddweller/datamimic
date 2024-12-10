# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.converter.converter import Converter


class MaskConverter(Converter):
    """
    Convert string data to mask
    Optional: Input a single character to be the mask char, default to '*'
    For example: convert 'foo' into ***'
    """

    def __init__(self, mask_char: str = "*"):
        if len(mask_char) != 1:
            raise ValueError("Mask character can only be a single character")
        self._mask_char = mask_char

    def convert(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"Converter Mask expect datatype 'string', but got value {value} with invalid datatype {type(value)}"
            )
        else:
            masked_string: str = self._mask_char * len(value)
            return masked_string
