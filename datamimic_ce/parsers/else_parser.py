# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_ELSE
from datamimic_ce.parsers.if_else_base_parser import IfElseBaseParser


class ElseParser(IfElseBaseParser):
    """
    Parse element "else" to ElseStatement
    """

    def __init__(
        self,
        element: Element,
        properties: dict,
    ):
        super().__init__(element, properties, valid_element_tag=EL_ELSE)
