# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from ast import literal_eval
from typing import Any


class StringUtil:
    @staticmethod
    def get_class_name_from_constructor_string(original_string: str) -> str:
        """
        Get converter name from constructor

        :param original_string:
        :return:
        """
        index_of_opening_parenthesis = original_string.find("(")

        return original_string[:index_of_opening_parenthesis] if index_of_opening_parenthesis != -1 else original_string

    @staticmethod
    def parse_constructor_string(constructor_string: str) -> tuple[str, dict[str, Any]]:
        """
        Get entity name and parameters from constructor

        :param constructor_string:
        :return:
        """
        constructor_string = constructor_string.strip()

        # Find positions of the opening and closing parentheses
        opening_parenthesis_index = constructor_string.find("(")
        closing_parenthesis_index = constructor_string.rfind(")")

        # Initialize entity name and parameters dictionary
        entity_name = ""
        parameters = {}

        if opening_parenthesis_index != -1:
            entity_name = constructor_string[:opening_parenthesis_index].strip()
            if closing_parenthesis_index != -1:
                parameters_string = constructor_string[
                    opening_parenthesis_index + 1 : closing_parenthesis_index
                ].strip()
            else:
                parameters_string = ""
        else:
            entity_name = constructor_string
            parameters_string = ""

        # Parse parameters string into a dictionary
        if parameters_string:
            param_list = parameters_string.split(",")
            for param in param_list:
                if "=" in param:
                    key_value_pair = param.split("=")
                    if len(key_value_pair) == 2:
                        key, value = key_value_pair
                        try:
                            parameters[key.strip()] = literal_eval(value.strip())
                        except (ValueError, SyntaxError):
                            parameters[key.strip()] = value.strip()

        return entity_name, parameters

    @staticmethod
    def validate_project_name(name: str) -> bool:
        """
        Validate project name for invalid characters and patterns.

        Args:
            name (str): Project name to validate

        Returns:
            bool: True if valid, False otherwise
        """
        import re

        # Check for valid characters (alphanumeric, dash, underscore)
        pattern = re.compile(r"^[a-zA-Z0-9_-]+$")
        return bool(pattern.match(name))
