# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.engine.dsl.model.values.structured.nested_key_model import NestedKeyModel
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.base.statement import Statement
from datamimic_ce.engine.dsl.statements.values.structured.nested_key_statement import NestedKeyStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_NESTED_KEY


class NestedKeyParser(StatementParser):
    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_NESTED_KEY,
        )

    def parse(
        self,
        descriptor_dir: Path,
        parent_stmt: Statement,
        *,
        profile_loader: ConnectionProfileLoader,
    ) -> NestedKeyStatement:
        """
        Parse element "part" to PartStatement
        :return:
        """
        # Parse sub elements
        from datamimic_ce.engine.dsl.parsers.base.dispatch import parse_sub_elements

        nested_key_stmt = NestedKeyStatement(self.validate_attributes(NestedKeyModel), parent_stmt)
        sub_stmt_list = parse_sub_elements(
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=nested_key_stmt,
            profile_loader=profile_loader,
        )
        nested_key_stmt.sub_statements = sub_stmt_list

        return nested_key_stmt
