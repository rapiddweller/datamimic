# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_ARRAY
from datamimic_ce.model.array_model import ArrayModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.array_statement import ArrayStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ArrayParser(StatementParser):
    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_ARRAY,
            class_factory_util=class_factory_util,
        )

    def parse(self, **kwargs) -> ArrayStatement:
        """
        Parse element "array" to ArrayStatement
        :return:
        """

        return ArrayStatement(self.validate_attributes(ArrayModel))
