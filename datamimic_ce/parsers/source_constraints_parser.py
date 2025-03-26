# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_SOURCE_CONSTRAINTS
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.source_constraints_statement import ConstraintsStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ConstraintsParser(StatementParser):
    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_SOURCE_CONSTRAINTS,
            class_factory_util=class_factory_util,
        )

    def parse(self, descriptor_dir: Path, parent_stmt: CompositeStatement) -> ConstraintsStatement:
        """
        Parse element "sourceConstraints" into ConstraintsStatement
        :return:
        """
        constraints_stmt = ConstraintsStatement(parent_stmt)
        sub_stmt_list = self._class_factory_util.get_parser_util_cls()().parse_sub_elements(
            class_factory_util=self._class_factory_util,
            descriptor_dir=descriptor_dir,
            element=self._element,
            properties=self._properties,
            parent_stmt=constraints_stmt,
        )
        constraints_stmt.sub_statements = sub_stmt_list
        return constraints_stmt
