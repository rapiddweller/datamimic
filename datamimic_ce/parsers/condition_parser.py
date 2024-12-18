# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.attribute_constants import ATTR_CONDITION
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.condition_statement import ConditionStatement
from datamimic_ce.statements.else_if_statement import ElseIfStatement
from datamimic_ce.statements.else_statement import ElseStatement
from datamimic_ce.statements.if_statement import IfStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ConditionParser(StatementParser):
    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=ATTR_CONDITION,
            class_factory_util=class_factory_util,
        )

    def parse(self, descriptor_dir: Path, parent_stmt: CompositeStatement) -> ConditionStatement:
        """
        Parse element "condition" to ConditionStatement.
        :return:
        """
        # Parse sub elements

        condition_stmt = ConditionStatement(parent_stmt)
        sub_stmt_list = self._class_factory_util.get_parser_util_cls()().parse_sub_elements(
            class_factory_util=self._class_factory_util,
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=condition_stmt,
        )
        self._check_valid_order_and_count(sub_stmt_list)

        condition_stmt.sub_statements = sub_stmt_list

        return condition_stmt

    @staticmethod
    def _check_valid_order_and_count(sub_stmt_list: list[Statement]):
        """
        Check order and count tag if, else-if, else.
        """
        found_if = False
        found_else = False

        for stmt in sub_stmt_list:
            if isinstance(stmt, IfStatement):
                if found_if:
                    raise ValueError("Fail while parsing <condition>. Only one tag <if> is allowed in <condition>.")
                found_if = True
            elif isinstance(stmt, ElseIfStatement):
                if not found_if:
                    raise ValueError("Fail while parsing <condition>. Must have <if> as the first tag.")
                if found_else:
                    raise ValueError("Fail while parsing <condition>. Tag <else> must be the last tag.")
            elif isinstance(stmt, ElseStatement):
                if not found_if:
                    raise ValueError("Fail while parsing <condition>. Must have <if> as the first tag.")
                if found_else:
                    raise ValueError("Fail while parsing <condition>. There can only be one tag <else> at most.")
                found_else = True
            else:
                raise ValueError(f"Invalid tag {stmt.__class__.__name__} in <condition>.")

        if not found_if:
            raise ValueError("Fail while parsing <condition>. Must have <if> as the first tag.")
