# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import xml.etree.ElementTree as ET
from pathlib import Path

from datamimic_ce.parsers.setup_parser import SetupParser
from datamimic_ce.statements.setup_statement import SetupStatement


class DescriptorParser:
    """
    Entry point or process parsing. Parse XML descriptor file into statements
    """

    @staticmethod
    def parse(
        descriptor_file_path: Path,
        properties: dict | None,
    ) -> SetupStatement:
        """
        Parsing descriptor file to RootStatement
        :descriptor_file_path:
        :return:
        """
        try:
            # Parse entry point descriptor file
            tree = ET.parse(descriptor_file_path)
            root = tree.getroot()

            # Use SetupParser to parse root element "setup"
            setup_parser = SetupParser(root, properties)
            root_stmt = setup_parser.parse(descriptor_file_path.parent)
            return root_stmt
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Descriptor file not found: '{descriptor_file_path.name}'") from e
