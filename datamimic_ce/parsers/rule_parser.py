# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_RULE
from datamimic_ce.model.rule_model import RuleModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.rule_statement import RuleStatement
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class RuleParser(StatementParser):
    """
    Parse element "rule" to RuleStatement
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(element, properties, valid_element_tag=EL_RULE, class_factory_util=class_factory_util)

    def parse(self, descriptor_dir: Path, parent_stmt: Statement) -> RuleStatement:
        """
        Parse element "xml-attribute" to XmlAttributeStatement
        :return:
        """

        return RuleStatement(self.validate_attributes(RuleModel))
