# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.flow.commands.echo_statement import EchoStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_ECHO


class EchoParser(StatementParser):
    """
    Parse element "echo" to EchoStatement
    """

    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_ECHO,
        )

    def parse(self, **kwargs: Any) -> EchoStatement:
        """
        Parse element "echo" to EchoStatement
        :return:
        """
        return EchoStatement(self._element.text)
