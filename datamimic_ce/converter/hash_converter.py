# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any, NoReturn

from datamimic_ce.converter.converter import Converter
from datamimic_ce.converter.converter_util import ConverterUtil
from datamimic_ce.enums.converter_enums import SupportHash, SupportOutputFormat


class HashConverter(Converter):
    """
    A converter to generate the hash of a string base on the hash type and the output format.
    Optionally, can enhance the hash with salt
    """

    def __init__(self, hash_type: str, output_format: str, salt: str | None = None):
        support_hashes = set(support_hash.value for support_hash in SupportHash)
        support_output_format = set(support_output.value for support_output in SupportOutputFormat)
        if hash_type.lower() not in support_hashes:
            raise TypeError(
                f"""
                HashConverter can only support hash type of {support_hashes} but recieved {hash_type}
                """
            )
        elif output_format.lower() not in support_output_format:
            raise TypeError(
                f"""
                HashConverter can only support output format of {support_output_format} but recieved {output_format}
                """
            )
        self._hash_type = hash_type
        self._output_format = output_format
        self._salt = salt

    def convert(self, value: Any) -> NoReturn | str:
        if not isinstance(value, str):
            raise ValueError(
                f"HashConverter expects data type 'string', but got value {value} "
                f"with an invalid datatype {type(value)}"
            )
        return ConverterUtil.get_hash_value(
            hash_type=self._hash_type,
            output_format=self._output_format,
            value=value,
            salt=self._salt,
        )
