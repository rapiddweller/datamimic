# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_ELSE_IF
from datamimic_ce.parsers.if_else_base_parser import IfElseBaseParser
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class ElseIfParser(IfElseBaseParser):
    """
    Parse element "else-if" to ElseIfStatement
    """

    def __init__(
        self,
        class_factory_util: BaseClassFactoryUtil,
        element: Element,
        properties: dict,
    ):
        super().__init__(class_factory_util, element, properties, valid_element_tag=EL_ELSE_IF)
