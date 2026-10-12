# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from datamimic_ce.engine.dsl.model.setup.include_model import IncludeModel
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.setup.include_statement import IncludeStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_INCLUDE


class IncludeParser(StatementParser):
    """
    Parse element "include" to IncludeStatement
    """

    def __init__(
        self,
        element: XmlElement,
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
