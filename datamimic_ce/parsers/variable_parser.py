# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_VARIABLE
from datamimic_ce.model.variable_model import VariableModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.statement import Statement
from datamimic_ce.statements.variable_statement import VariableStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class VariableParser(StatementParser):
    """
    Parse element "variable" into VariableStatement
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_VARIABLE,
            class_factory_util=class_factory_util,
        )

    def parse(self, parent_stmt: Statement, has_parent_setup: bool | None = False) -> VariableStatement:
        """
        Parse element "variable" into VariableStatement
        :return:
        """
        return VariableStatement(self.validate_attributes(VariableModel), parent_stmt, has_parent_setup)
