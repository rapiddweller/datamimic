# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import ast
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path
from typing import Any
from xml.sax.saxutils import unescape as stdlib_unescape

import toml

_SAFE_PARSE_XML_ENTITIES = {
    "&quot;": '"',  # Corrected: map &quot; to a single double quote character
    "&apos;": "'",
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
}


class XMLValidator:
    """Validator for DATAMIMIC XML descriptors."""

    def __init__(self):
        """Initialize the XML validator."""
        self.errors: list[str] = []

    def validate_descriptor(self, file_path: Path) -> bool:
        """
        Validate a DATAMIMIC XML descriptor file.

        Args:
            file_path: Path to the XML descriptor file

        Returns:
            bool: True if validation successful, False otherwise
        """
        self.errors = []  # Reset errors for new validation

        try:
            # Read and clean the XML content
            with open(file_path, encoding="utf-8") as f:
                xml_content = f.read().strip()

            # Parse XML
            try:
                tree = ET.fromstring(xml_content)
            except ET.ParseError as e:
                self.errors.append(f"XML parsing error: {str(e)}")
                return False

            # Check root element
            if tree.tag != "setup":
                self.errors.append("Root element must be <setup>")
                return False

            # Validate generate elements
            generate_elements = tree.findall(".//generate")
            if not generate_elements:
                self.errors.append("At least one <generate> element is required")
                return False

            for generate in generate_elements:
                self._validate_generate_element(generate)

            # Check for info.toml if it exists
            info_toml_path = file_path.parent / "info.toml"
            if info_toml_path.exists():
                self._validate_info_toml(info_toml_path)

            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"Validation error: {str(e)}")
            return False

    def _validate_generate_element(self, element: ET.Element) -> None:
        """
        Validate a generate element in the descriptor.

        Args:
            element: The generate element to validate
        """
        # Check required attributes
        if "name" not in element.attrib:
            self.errors.append("Generate element must have a 'name' attribute")

        # Check for either variables or keys
        variables = element.findall("variable")
        keys = element.findall("key")
        if not variables and not keys:
            self.errors.append("Generate element must have at least one variable or key")

    def _validate_info_toml(self, file_path: Path) -> None:
        """
        Validate info.toml file structure.

        Args:
            file_path: Path to the info.toml file
        """
        try:
            info = toml.load(file_path)

            # Required fields
            required_fields = ["projectName", "description", "dependencies", "usage"]
            for field in required_fields:
                if field not in info:
                    self.errors.append(f"info.toml is missing required field: {field}")
                elif not isinstance(info[field], str):
                    self.errors.append(f"info.toml field '{field}' must be a string")

            # Validate project name format
            if "projectName" in info:
                project_name = info["projectName"]
                if not project_name.replace("-", "").replace("_", "").isalnum():
                    self.errors.append("Project name can only contain letters, numbers, underscores, and hyphens")

        except toml.TomlDecodeError as e:
            self.errors.append(f"Error parsing info.toml: {str(e)}")
        except Exception as e:
            self.errors.append(f"Error validating info.toml: {str(e)}")

    def get_errors(self) -> list[str]:
        """
        Get the list of validation errors.

        Returns:
            List[str]: List of validation error messages
        """
        return self.errors


def safe_parse_generator_param(param_value: str, evaluator: Callable[[str], Any] | None = None) -> Any:
    """
    Safely parses a string parameter value from XML, which might be XML escaped,
    and attempts to evaluate it as a Python literal (e.g., list, dict, number, string, boolean, None).

    Handles cases such as:
    - "123" -> 123
    - "'hello'" -> "hello"
    - "\\"hello\\"" -> "hello"
    - "[1, 2, 3]" -> [1, 2, 3]
    - "{'a': 1}" -> {'a': 1}
    - "None" -> None
    - "True" -> True
    - "&quot;[1, 2, 3]&quot;" -> unescapes to "\"[1, 2, 3]\"", then evaluates inner "[1, 2, 3]" to [1, 2, 3]
    - "'[1, 2, 3]'" -> unescapes to "'[1, 2, 3]'", then evaluates inner "[1, 2, 3]" to [1, 2, 3]

    If an optional `evaluator` function is provided, this function will be used to attempt
    to evaluate the string if it's not a simple Python literal but might be an expression
    (e.g., "[0.1]*10" or "[x for x in range(5)]"). If evaluation via `evaluator` fails,
    the string (after unescaping) is returned.

    If parsing as a literal fails and no evaluator is provided (or the evaluator fails),
    the unescaped string is returned.
    """
    if not isinstance(param_value, str):
        return param_value  # Already parsed or not a string

    try:
        # Step 1: Unescape XML entities.
        processed_value = stdlib_unescape(param_value, entities=_SAFE_PARSE_XML_ENTITIES)
    except Exception:
        # Fallback if unescaping has an issue, though unlikely for string inputs
        processed_value = param_value

    try:
        # Step 2: Attempt to evaluate as a Python literal.
        evaluated_value = ast.literal_eval(processed_value)

        if isinstance(evaluated_value, str):
            # The first literal_eval resulted in a string. This could be:
            # 1. A string that itself represents a literal (e.g., param_value was "'[1,2,3]'").
            # 2. A string that is an expression (e.g., param_value was "'[0.1]*10'").
            # 3. A plain string (e.g., param_value was "'actual_string'").
            try:
                # Try to evaluate this string as a literal again (handles case 1)
                return ast.literal_eval(evaluated_value)
            except (ValueError, SyntaxError, TypeError):
                # If the inner evaluation fails, it means the string was not a simple literal.
                # It could be an expression (case 2) or a plain string that just happens
                # to be the content (case 3, e.g. evaluated_value is "[0.1]*10" or "actual_string").
                if evaluator:
                    try:
                        return evaluator(evaluated_value)  # Try to evaluate as expression
                    except Exception:
                        # Evaluator failed, so it's likely just a plain string.
                        return evaluated_value
                return evaluated_value  # No evaluator, return the string
        else:
            # The first evaluation yielded a non-string literal (list, dict, number, bool, None)
            return evaluated_value
    except (ValueError, SyntaxError, TypeError):
        # If not a valid Python literal string (e.g., "some_text", or an expression like "[0.1]*10" without quotes),
        # return the processed (unescaped) string itself, unless an evaluator can handle it.
        if evaluator:
            try:
                return evaluator(processed_value)  # Try to evaluate as expression
            except Exception:
                # Evaluator failed, so it's likely just a plain string.
                return processed_value
        return processed_value
