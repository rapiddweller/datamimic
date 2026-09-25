# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.constants.element_constants import EL_VARIABLE
from datamimic_ce.engine.dsl.model.variable_model import VariableModel
from datamimic_ce.engine.dsl.parsers.statement_parser import StatementParser
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.statements.variable_statement import VariableStatement
from datamimic_ce.engine.dsl.xml import XmlElement


class VariableParser(StatementParser):
    """
    Parse element "variable" into VariableStatement
    """

    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_VARIABLE,
        )

    def parse(self, parent_stmt: Statement, has_parent_setup: bool | None = False) -> VariableStatement:
        """
        Parse element "variable" into VariableStatement
        :return:
        """
        return VariableStatement(self.validate_attributes(VariableModel), parent_stmt, has_parent_setup)
