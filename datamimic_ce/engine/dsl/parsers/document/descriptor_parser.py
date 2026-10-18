# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from dataclasses import replace
from pathlib import Path
from typing import Literal

from datamimic_ce.engine.dsl.parsers import registry  # noqa: F401  # package composition
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.engine.dsl.parsers.input.xml import parse_xml_file, parse_xml_source
from datamimic_ce.engine.dsl.parsers.setup.setup_parser import SetupParser
from datamimic_ce.engine.dsl.statements.setup.setup_statement import SetupStatement
from datamimic_ce.errors.base import UserErrorBase
from datamimic_ce.errors.context import DescriptorLocation


class DescriptorParser:
    """
    Entry point or process parsing. Parse XML descriptor file into statements
    """

    @staticmethod
    def parse(
        descriptor_file_path: Path,
        properties: dict[str, str] | dict[str, object] | None,
        runtime_environment: Literal["development", "production"],
        *,
        profile_loader: ConnectionProfileLoader,
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
            root_stmt = setup_parser.parse(descriptor_file_path.parent, profile_loader=profile_loader)
            return root_stmt
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Descriptor file not found: '{descriptor_file_path.name}'") from e

    @staticmethod
    def parse_xml(
        xml: str,
        descriptor_file_path: Path,
        properties: dict[str, str] | dict[str, object] | None,
        runtime_environment: Literal["development", "production"],
        *,
        profile_loader: ConnectionProfileLoader,
        logical_descriptor_path: str | None = None,
    ) -> SetupStatement:
        """Parse in-memory XML with the same descriptor-relative resource identity."""
        root = parse_xml_source(xml)
        try:
            setup_parser = SetupParser(root, properties, runtime_environment)
            return setup_parser.parse(descriptor_file_path.parent, profile_loader=profile_loader)
        except UserErrorBase as error:
            location = error.location or DescriptorLocation(element_tag="setup")
            error.location = replace(location, descriptor_path=logical_descriptor_path or descriptor_file_path.name)
            raise
