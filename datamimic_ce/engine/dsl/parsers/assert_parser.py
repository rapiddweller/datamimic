# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from typing import Any

from datamimic_ce.engine.dsl.constants.element_constants import EL_ASSERT
from datamimic_ce.engine.dsl.model.assert_model import AssertModel
from datamimic_ce.engine.dsl.parsers.statement_parser import StatementParser
from datamimic_ce.engine.dsl.statements.assert_statement import AssertStatement
from datamimic_ce.engine.dsl.xml import XmlElement


class AssertParser(StatementParser):
    """
    Parse element "assert" to AssertStatement
    """

    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_ASSERT,
        )

    def parse(self, **kwargs: Any) -> AssertStatement:
        return AssertStatement(self.validate_attributes(AssertModel))
