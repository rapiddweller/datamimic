# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_ECHO
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.echo_statement import EchoStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class EchoParser(StatementParser):
    """
    Parse element "echo" to EchoStatement
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
            valid_element_tag=EL_ECHO,
            class_factory_util=class_factory_util,
        )

    def parse(self, **kwargs: Any) -> EchoStatement:
        """
        Parse element "echo" to EchoStatement
        :return:
        """
        return EchoStatement(self._element.text)
