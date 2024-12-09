# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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
