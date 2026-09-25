# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.engine.dsl.constants.element_constants import EL_IF
from datamimic_ce.engine.dsl.parsers.if_else_base_parser import IfElseBaseParser
from datamimic_ce.engine.dsl.xml import XmlElement


class IfParser(IfElseBaseParser):
    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_IF,
        )
