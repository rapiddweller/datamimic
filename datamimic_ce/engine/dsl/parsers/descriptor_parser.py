# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from typing import Literal

from datamimic_ce.engine.dsl.parsers.setup_parser import SetupParser
from datamimic_ce.engine.dsl.statements.setup_statement import SetupStatement
from datamimic_ce.engine.dsl.xml import parse_xml_file


class DescriptorParser:
    """
    Entry point or process parsing. Parse XML descriptor file into statements
    """

    @staticmethod
    def parse(
        descriptor_file_path: Path,
        properties: dict | None,
        runtime_environment: Literal["development", "production"],
    ) -> SetupStatement:
        """
        Parsing descriptor file to RootStatement
        :descriptor_file_path:
        :return:
        """
        try:
            # Parse entry point descriptor file
            root = parse_xml_file(descriptor_file_path)

            # Use SetupParser to parse root element "setup"
            setup_parser = SetupParser(root, properties, runtime_environment)
            root_stmt = setup_parser.parse(descriptor_file_path.parent)
            return root_stmt
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Descriptor file not found: '{descriptor_file_path.name}'") from e
