# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_INCLUDE
from datamimic_ce.model.include_model import IncludeModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.include_statement import IncludeStatement


class IncludeParser(StatementParser):
    """
    Parse element "include" to IncludeStatement
    """

    def __init__(
        self,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_INCLUDE,
        )

    def parse(self) -> IncludeStatement:
        """
        Parse element "include" to IncludeStatement
        :return:
        """
        return IncludeStatement(self.validate_attributes(IncludeModel))
