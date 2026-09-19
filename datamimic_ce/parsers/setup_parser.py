# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.attribute_constants import ATTR_PSEUDONYMIZATION_KEY
from datamimic_ce.constants.element_constants import EL_SETUP
from datamimic_ce.model.setup_model import SetupModel
from datamimic_ce.parsers.parser_util import ParserUtil
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.setup_statement import SetupStatement


class SetupParser(StatementParser):
    """
    Parse element "setup" into RootStatement
    """

    def __init__(self, element: Element, properties: dict | None):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_SETUP,
        )

    def parse(self, descriptor_dir: Path) -> SetupStatement:
        """
        Parse element "setup" into RootStatement
        :return:
        """
        # Parse sub elements

        raw_key = self._element.get(ATTR_PSEUDONYMIZATION_KEY)
        if raw_key is not None:
            property_name = ParserUtil.property_reference(raw_key)
            if property_name is None:
                raise ValueError(f"{ATTR_PSEUDONYMIZATION_KEY} must reference a property")
            resolved = ParserUtil.retrieve_element_attributes(
                {ATTR_PSEUDONYMIZATION_KEY: raw_key}, self._properties
            )[ATTR_PSEUDONYMIZATION_KEY]
            if resolved == raw_key:
                raise ValueError(f"{ATTR_PSEUDONYMIZATION_KEY} property '{property_name}' is missing")
        setup_stmt = SetupStatement(self.validate_attributes(SetupModel))
        sub_stmt_list = ParserUtil.parse_sub_elements(
            descriptor_dir,
            self._element,
            self._properties,
            setup_stmt,
        )
        setup_stmt.sub_statements = sub_stmt_list

        return setup_stmt
