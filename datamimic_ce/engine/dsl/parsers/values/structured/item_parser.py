# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.engine.dsl.model.values.structured.item_model import ItemModel
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.values.structured.item_statement import ItemStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_ITEM


class ItemParser(StatementParser):
    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_ITEM,
        )

    def parse(
        self,
        descriptor_dir: Path,
        *,
        profile_loader: ConnectionProfileLoader,
    ) -> ItemStatement:
        """
        Parse element "item" to ItemStatement
        :return:
        """
        # Parse sub elements
        from datamimic_ce.engine.dsl.parsers.base.dispatch import parse_sub_elements

        item_stmt = ItemStatement(self.validate_attributes(ItemModel))
        sub_stmt_list = parse_sub_elements(
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=item_stmt,
            profile_loader=profile_loader,
        )
        item_stmt.sub_statements = sub_stmt_list

        return item_stmt
