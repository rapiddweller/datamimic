# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.engine.dsl.model.values.structured.list_model import ListModel
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.values.structured.list_statement import ListStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_LIST


class ListParser(StatementParser):
    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_LIST,
        )

    def parse(
        self,
        descriptor_dir: Path,
        *,
        profile_loader: ConnectionProfileLoader,
    ) -> ListStatement:
        """
        Parse element "list" to ListStatement
        :return:
        """
        # Parse sub elements
        from datamimic_ce.engine.dsl.parsers.base.dispatch import parse_sub_elements

        list_stmt = ListStatement(self.validate_attributes(ListModel))
        sub_stmt_list = parse_sub_elements(
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=list_stmt,
            profile_loader=profile_loader,
        )
        list_stmt.sub_statements = sub_stmt_list

        return list_stmt
