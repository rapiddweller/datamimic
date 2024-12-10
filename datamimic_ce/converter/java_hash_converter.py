# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.converter.converter import Converter


class JavaHashConverter(Converter):
    """Replicate the Java Hash function"""

    def convert(self, value: str) -> str:
        h = 0
        for char in value:
            h = (31 * h + ord(char)) & 0xFFFFFFFF
        return "%08x" % (h & 0xFFFFFFFF)
