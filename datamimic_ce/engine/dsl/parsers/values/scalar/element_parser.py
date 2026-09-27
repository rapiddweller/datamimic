# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.values.scalar.element_model import ElementModel
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.statements.values.scalar.element_statement import ElementStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_ELEMENT


class ElementParser(StatementParser):
    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_ELEMENT,
        )

    def parse(self, parent_stmt: Statement) -> ElementStatement:
        """
        Parse element "xml-attribute" to XmlAttributeStatement
        :return:
        """

        return ElementStatement(self.validate_attributes(ElementModel), parent_stmt)
