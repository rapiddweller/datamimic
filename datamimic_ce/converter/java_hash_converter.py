# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from datamimic_ce.converter.converter import Converter


class JavaHashConverter(Converter):
    """Replicate the Java Hash function"""

    def convert(self, value: str) -> str:
        h = 0
        for char in value:
            h = (31 * h + ord(char)) & 0xFFFFFFFF
        return "%08x" % (h & 0xFFFFFFFF)
