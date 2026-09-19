# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_WHILE
from datamimic_ce.model.while_model import WhileModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.condition_statement import ConditionStatement
from datamimic_ce.statements.if_statement import IfStatement
from datamimic_ce.statements.while_statement import WhileStatement


class WhileParser(StatementParser):
    """Parse element "while" into a WhileStatement (a per-row loop over its child statements)."""

    def __init__(self, element: Element, properties: dict):
        super().__init__(element, properties, valid_element_tag=EL_WHILE)

    def parse(self, descriptor_dir: Path, parent_stmt: CompositeStatement) -> WhileStatement:
        from datamimic_ce.parsers.parser_util import ParserUtil

        # A <while> body accepts whatever the enclosing composite (<generate>/<nestedKey>) accepts —
        # walk up through any condition/if/while wrappers to that composite, like IfElseBaseParser.
        composite_stmt: Any = parent_stmt
        while isinstance(composite_stmt, ConditionStatement | IfStatement | WhileStatement):
            composite_stmt = composite_stmt.parent_stmt
        valid_sub_ele_set = ParserUtil.get_valid_sub_elements_set_by_tag(
            ParserUtil.get_element_tag_by_statement(composite_stmt)
        )
        self.set_and_validate_valid_sub_elements(valid_sub_ele_set)

        while_stmt = WhileStatement(self.validate_attributes(WhileModel), parent_stmt)
        while_stmt.sub_statements = ParserUtil.parse_sub_elements(
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=while_stmt,
        )
        return while_stmt
