# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import xml.etree.ElementTree as ET
from pathlib import Path

from datamimic_ce.parsers.setup_parser import SetupParser
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class DescriptorParser:
    """
    Entry point or process parsing. Parse XML descriptor file into statements
    """

    @staticmethod
    def parse(
        cls_factory_util: BaseClassFactoryUtil,
        descriptor_file_path: Path,
        properties: dict | None = None,
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
            setup_parser = SetupParser(cls_factory_util, root, properties)
            root_stmt = setup_parser.parse(descriptor_file_path.parent)
            return root_stmt
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Descriptor file not found: '{descriptor_file_path.name}'") from e
