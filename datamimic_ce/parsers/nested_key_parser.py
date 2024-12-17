# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_NESTED_KEY
from datamimic_ce.model.nested_key_model import NestedKeyModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.nested_key_statement import NestedKeyStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class NestedKeyParser(StatementParser):
    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_NESTED_KEY,
            class_factory_util=class_factory_util,
        )

    def parse(self, descriptor_dir: Path, parent_stmt: Statement) -> NestedKeyStatement:
        """
        Parse element "part" to PartStatement
        :return:
        """
        # Parse sub elements

        nested_key_stmt = NestedKeyStatement(self.validate_attributes(NestedKeyModel), parent_stmt)
        sub_stmt_list = self._class_factory_util.get_parser_util_cls()().parse_sub_elements(
            class_factory_util=self._class_factory_util,
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=nested_key_stmt,
        )
        nested_key_stmt.sub_statements = sub_stmt_list

        return nested_key_stmt
