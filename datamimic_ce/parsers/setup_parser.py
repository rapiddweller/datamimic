# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

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

        setup_stmt = SetupStatement(self.validate_attributes(SetupModel))
        sub_stmt_list = ParserUtil.parse_sub_elements(
            descriptor_dir,
            self._element,
            self._properties,
            setup_stmt,
        )
        setup_stmt.sub_statements = sub_stmt_list

        return setup_stmt
