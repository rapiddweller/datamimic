# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from typing import cast
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_KEY
from datamimic_ce.model.key_model import KeyModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.composite_statement import CompositeStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class KeyParser(StatementParser):
    """
    Parse element "attribute" into AttributeStatement
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_KEY,
            class_factory_util=class_factory_util,
        )

    def parse(self, descriptor_dir: Path, parent_stmt: Statement) -> KeyStatement:
        """
        Parse element "attribute" into AttributeStatement
        :return:
        """

        key_stmt = KeyStatement(self.validate_attributes(KeyModel), cast(CompositeStatement, parent_stmt))
        sub_stmt_list = self._class_factory_util.get_parser_util_cls()().parse_sub_elements(
            self._class_factory_util,
            descriptor_dir,
            self._element,
            self._properties,
            parent_stmt=key_stmt,
        )
        key_stmt.sub_statements = sub_stmt_list

        return key_stmt
