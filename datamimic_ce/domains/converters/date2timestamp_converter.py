# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datetime import datetime

from datamimic_ce.domains.converters.converter import Converter
from datamimic_ce.domains.domain_core.runtime import to_epoch_utc


class Date2TimestampConverter(Converter):
    """
    Convert datetime data to timestamp (float)
    """

    def convert(self, value: object) -> int:
        if not isinstance(value, datetime):
            raise ValueError(
                f"Converter Date2Timestamp expect datatype 'datetime', "
                f"but got value {value} with invalid datatype {type(value)}"
            )

        return int(to_epoch_utc(value))
