# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_GENERATOR
from datamimic_ce.model.generator_model import GeneratorModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.generator_statement import GeneratorStatement


class GeneratorParser(StatementParser):
    """
    Parse element "generator" to GeneratorStatement
    """

    def __init__(
        self,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_GENERATOR,
        )

    def parse(self) -> GeneratorStatement:
        """
        Parse element "generator" to GeneratorStatement
        :return:
        """
        return GeneratorStatement(self.validate_attributes(GeneratorModel))
