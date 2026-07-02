# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.converter.converter import Converter


class SubstringConverter(Converter):
    """Extract value[start:end] with python slice semantics (negatives count from the end).

    ``Substring(-4)`` = the last four characters — the classic anonymization tail-extract
    (Benerator's ``SubstringExtractor(from, to)`` counterpart).
    """

    def __init__(self, start: int, end: int | None = None):
        if not isinstance(start, int) or (end is not None and not isinstance(end, int)):
            raise ValueError(f"Converter Substring expects integer bounds, got start={start!r}, end={end!r}")
        self._start = start
        self._end = end

    def convert(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"Converter Substring expects datatype 'string', but got value {value} "
                f"with invalid datatype {type(value)}"
            )
        return value[self._start : self._end]
