# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_EXECUTE
from datamimic_ce.model.execute_model import ExecuteModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.execute_statement import ExecuteStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ExecuteParser(StatementParser):
    """
    Parse element "execute" to ExecuteStatement
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
            valid_element_tag=EL_EXECUTE,
            class_factory_util=class_factory_util,
        )
        if element.text:
            raise ValueError("Element <execute> cannot contain text. Please put script into files.")

    def parse(self, **kwargs) -> ExecuteStatement:
        """
        Parse element "memstore" to MemstoreStatement
        :return:
        """
        return ExecuteStatement(self.validate_attributes(ExecuteModel))
