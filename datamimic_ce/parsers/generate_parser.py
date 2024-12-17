# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_GENERATE
from datamimic_ce.model.generate_model import GenerateModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class GenerateParser(StatementParser):
    """
    Parse element "generate" into GenerateStatement
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
            valid_element_tag=EL_GENERATE,
            class_factory_util=class_factory_util,
        )

    def parse(self, descriptor_dir: Path, parent_stmt: Statement, lazy_parse: bool = False) -> GenerateStatement:
        """
        Parse element "generate" into GenerateStatement
        :return:
        """
        model = self.validate_attributes(GenerateModel)

        # Parse sub elements

        gen_stmt = GenerateStatement(model, parent_stmt)
        sub_stmt_list = self._class_factory_util.get_parser_util_cls()().parse_sub_elements(
            self._class_factory_util,
            descriptor_dir,
            self._element,
            self._properties,
            gen_stmt,
        )
        gen_stmt.sub_statements = sub_stmt_list
        return gen_stmt
