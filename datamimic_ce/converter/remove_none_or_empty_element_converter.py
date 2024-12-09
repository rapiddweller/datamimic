# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import copy
from typing import Dict, List, Union, Any

from datamimic_ce.converter.converter import Converter


class RemoveNoneOrEmptyElementConverter(Converter):
    """
    Removes None or empty elements from nested data structures efficiently.
    """

    __slots__ = ()  # Optimize memory usage

    EMPTY_VALUES: list = list((None, "", [], {}))

    def convert(self, value: Union[List[Any], Dict[str, Any]]) -> Union[List[Any], Dict[str, Any]]:
        """Recursively removes empty elements."""
        # Early return for primitive types
        if not isinstance(value, (list, dict)):
            return value

        # Dispatch to specialized handlers
        # copy of value to avoid modifying while iterating
        copy_value = copy.deepcopy(value)
        return self._convert_list(copy_value) if isinstance(copy_value, list) else self._convert_dict(copy_value)

    def _convert_list(self, values: List[Any]) -> List[Any]:
        """Process list elements with list comprehension."""
        # Single-pass list comprehension with inline conversion
        result = []
        for item in values:
            if item not in self.EMPTY_VALUES:
                converted = self.convert(item)
                if converted not in self.EMPTY_VALUES:
                    result.append(converted)
        return result

    def _convert_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process dictionary with minimal copying."""
        # Create new dict directly with filtered items
        result = {}
        for key, value in data.items():
            if value not in self.EMPTY_VALUES:
                converted = self.convert(value)
                if converted not in self.EMPTY_VALUES:
                    result[key] = converted
        return result
