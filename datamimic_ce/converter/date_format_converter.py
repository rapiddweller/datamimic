# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datetime import datetime

from datamimic_ce.converter.converter import Converter


class DateFormatConverter(Converter):
    def __init__(self, format_str: str):
        self._format = format_str

    def convert(self, value: datetime) -> str:
        if not isinstance(value, datetime):
            raise ValueError(f"DateFormat converter expects datetime, got {type(value).__name__}: {value!r}")
        return value.strftime(self._format)
