# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

from datamimic_ce.model.else_if_model import ElseIfModel
from datamimic_ce.model.else_model import ElseModel
from datamimic_ce.model.if_model import IfModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.condition_statement import ConditionStatement
from datamimic_ce.statements.else_if_statement import ElseIfStatement
from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.statements.if_statement import IfStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class IfElseBaseParser(StatementParser, ABC):
    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
        valid_element_tag: str,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=valid_element_tag,
            class_factory_util=class_factory_util,
        )

    def parse(
        self, descriptor_dir: Path, parent_stmt: ConditionStatement
    ) -> IfStatement | ElseIfStatement | ElseStatement:
        # Retrieve the root composite statement
        composite_stmt: Any = parent_stmt
        while isinstance(composite_stmt, ConditionStatement | IfStatement):
            composite_stmt = composite_stmt.parent_stmt
        # Get valid sub elements of the composite statement
        valid_sub_ele_set = self._class_factory_util.get_parser_util_cls().get_valid_sub_elements_set_by_tag(
            self._class_factory_util.get_parser_util_cls().get_element_tag_by_statement(composite_stmt)
        )
        # Validate sub elements
        self._validate_sub_elements(valid_sub_ele_set, composite_stmt)

        parsed_stmt: IfStatement | ElseIfStatement | ElseStatement
        match self._valid_element_tag:
            case "if":
                parsed_stmt = IfStatement(self.validate_attributes(IfModel), parent_stmt)
            case "else-if":
                parsed_stmt = ElseIfStatement(self.validate_attributes(ElseIfModel), parent_stmt)
            case "else":
                parsed_stmt = ElseStatement(self.validate_attributes(ElseModel), parent_stmt)
            case _:
                raise ValueError(f"Invalid element tag for IfElseBaseParser: {self._valid_element_tag}")

        sub_stmt_list = self._class_factory_util.get_parser_util_cls()().parse_sub_elements(
            class_factory_util=self._class_factory_util,
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=parsed_stmt,
        )
        parsed_stmt.sub_statements = sub_stmt_list

        return parsed_stmt
