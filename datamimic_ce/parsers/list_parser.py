# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_LIST
from datamimic_ce.model.list_model import ListModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.list_statement import ListStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ListParser(StatementParser):
    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_LIST,
            class_factory_util=class_factory_util,
        )

    def parse(self, descriptor_dir: Path) -> ListStatement:
        """
        Parse element "list" to ListStatement
        :return:
        """
        # Parse sub elements

        list_stmt = ListStatement(self.validate_attributes(ListModel))
        sub_stmt_list = self._class_factory_util.get_parser_util_cls()().parse_sub_elements(
            class_factory_util=self._class_factory_util,
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=list_stmt,
        )
        list_stmt.sub_statements = sub_stmt_list

        return list_stmt
