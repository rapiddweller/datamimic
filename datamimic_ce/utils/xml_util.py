# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import xml.etree.ElementTree as ET
from pathlib import Path

import toml


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
