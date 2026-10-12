# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.model.setup.generators.generator_model import GeneratorModel
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.setup.generator_statement import GeneratorStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_GENERATOR


class GeneratorParser(StatementParser):
    """
    Parse element "generator" to GeneratorStatement
    """

    def __init__(
        self,
        element: XmlElement,
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
