# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
from typing import Any

from datamimic_ce.converter.converter import Converter


class RemoveNoneOrEmptyElementConverter(Converter):
    """
    Removes None or empty elements from nested data structures efficiently.
    """

    __slots__ = ()  # Optimize memory usage

    EMPTY_VALUES: list = list((None, "", [], {}))

    def convert(self, value: list[Any] | dict[str, Any]) -> list[Any] | dict[str, Any]:
        """Recursively removes empty elements."""
        # Early return for primitive types
        if not isinstance(value, list | dict):
            return value

        # Dispatch to specialized handlers
        # copy of value to avoid modifying while iterating
        copy_value = copy.deepcopy(value)
        return self._convert_list(copy_value) if isinstance(copy_value, list) else self._convert_dict(copy_value)

    def _convert_list(self, values: list[Any]) -> list[Any]:
        """Process list elements with list comprehension."""
        # Single-pass list comprehension with inline conversion
        result = []
        for item in values:
            if item not in self.EMPTY_VALUES:
                converted = self.convert(item)
                if converted not in self.EMPTY_VALUES:
                    result.append(converted)
        return result

    def _convert_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process dictionary with minimal copying."""
        # Create new dict directly with filtered items
        result = {}
        for key, value in data.items():
            if value not in self.EMPTY_VALUES:
                converted = self.convert(value)
                if converted not in self.EMPTY_VALUES:
                    result[key] = converted
        return result
