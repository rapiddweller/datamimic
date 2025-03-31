# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_ITEM
from datamimic_ce.model.item_model import ItemModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.item_statement import ItemStatement


class ItemParser(StatementParser):
    def __init__(
        self,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_ITEM,
        )

    def parse(self, descriptor_dir: Path) -> ItemStatement:
        """
        Parse element "item" to ItemStatement
        :return:
        """
        # Parse sub elements
        from datamimic_ce.parsers.parser_util import ParserUtil

        item_stmt = ItemStatement(self.validate_attributes(ItemModel))
        sub_stmt_list = ParserUtil.parse_sub_elements(
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=item_stmt,
        )
        item_stmt.sub_statements = sub_stmt_list

        return item_stmt
