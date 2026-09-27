# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.engine.dsl.model.flow.loops.while_model import WhileModel
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.condition_statement import ConditionStatement
from datamimic_ce.engine.dsl.statements.flow.branches.if_statement import IfStatement
from datamimic_ce.engine.dsl.statements.flow.loops.while_statement import WhileStatement
from datamimic_ce.engine.dsl.statements.statement import Statement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_WHILE


class WhileParser(StatementParser):
    """Parse element "while" into a WhileStatement (a per-row loop over its child statements)."""

    def __init__(self, element: XmlElement, properties: dict):
        super().__init__(element, properties, valid_element_tag=EL_WHILE)

    def parse(
        self,
        descriptor_dir: Path,
        parent_stmt: CompositeStatement,
        *,
        profile_loader: ConnectionProfileLoader,
    ) -> WhileStatement:
        from datamimic_ce.engine.dsl.parsers.base.dispatch import (
            get_element_tag_by_statement,
            get_valid_sub_elements_set_by_tag,
            parse_sub_elements,
        )

        # A <while> body accepts whatever the enclosing composite (<generate>/<nestedKey>) accepts —
        # walk up through any condition/if/while wrappers to that composite, like IfElseBaseParser.
        composite_stmt: Statement | None = parent_stmt
        while isinstance(composite_stmt, ConditionStatement | IfStatement | WhileStatement):
            composite_stmt = composite_stmt.parent_stmt
        if composite_stmt is None:
            raise ValueError("<while> statement has no enclosing composite")
        valid_sub_ele_set = get_valid_sub_elements_set_by_tag(get_element_tag_by_statement(composite_stmt))
        self.set_and_validate_valid_sub_elements(valid_sub_ele_set)

        while_stmt = WhileStatement(self.validate_attributes(WhileModel), parent_stmt)
        while_stmt.sub_statements = parse_sub_elements(
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=while_stmt,
            profile_loader=profile_loader,
        )
        return while_stmt
