# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from datamimic_ce.model.else_if_model import ElseIfModel
from datamimic_ce.model.if_model import IfModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.condition_statement import ConditionStatement
from datamimic_ce.statements.else_if_statement import ElseIfStatement
from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.statements.if_statement import IfStatement


class IfElseBaseParser(StatementParser, ABC):
    def __init__(
        self,
        element: Element,
        properties: dict,
        valid_element_tag: str,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=valid_element_tag,
        )

    def parse(
        self, descriptor_dir: Path, parent_stmt: ConditionStatement
    ) -> IfStatement | ElseIfStatement | ElseStatement:
        from datamimic_ce.parsers.parser_util import ParserUtil

        # Retrieve the root composite statement
        composite_stmt: Any = parent_stmt
        while isinstance(composite_stmt, ConditionStatement | IfStatement):
            composite_stmt = composite_stmt.parent_stmt
        # Get valid sub elements of the composite statement
        valid_sub_ele_set = ParserUtil.get_valid_sub_elements_set_by_tag(
            ParserUtil.get_element_tag_by_statement(composite_stmt)
        )
        # Validate sub elements
        self.set_and_validate_valid_sub_elements(valid_sub_ele_set)

        parsed_stmt: IfStatement | ElseIfStatement | ElseStatement
        match self._valid_element_tag:
            case "if":
                parsed_stmt = IfStatement(self.validate_attributes(IfModel), parent_stmt)
            case "else-if":
                parsed_stmt = ElseIfStatement(self.validate_attributes(ElseIfModel), parent_stmt)
            case "else":
                parsed_stmt = ElseStatement(parent_stmt)
            case _:
                raise ValueError(f"Invalid element tag for IfElseBaseParser: {self._valid_element_tag}")

        sub_stmt_list = ParserUtil.parse_sub_elements(
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=parsed_stmt,
        )
        parsed_stmt.sub_statements = sub_stmt_list

        return parsed_stmt
