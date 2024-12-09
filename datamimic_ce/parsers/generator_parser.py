# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_GENERATOR
from datamimic_ce.model.generator_model import GeneratorModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.generator_statement import GeneratorStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class GeneratorParser(StatementParser):
    """
    Parse element "generator" to GeneratorStatement
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
            valid_element_tag=EL_GENERATOR,
            class_factory_util=class_factory_util,
        )

    def parse(self) -> GeneratorStatement:
        """
        Parse element "generator" to GeneratorStatement
        :return:
        """
        return GeneratorStatement(self.validate_attributes(GeneratorModel))
