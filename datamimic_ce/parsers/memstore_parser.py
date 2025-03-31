# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_MEMSTORE
from datamimic_ce.model.memstore_model import MemstoreModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.memstore_statement import MemstoreStatement


class MemstoreParser(StatementParser):
    """
    Parse element "memstore" to MemstoreStatement
    """

    def __init__(
        self,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_MEMSTORE,
        )

    def parse(self) -> MemstoreStatement:
        """
        Parse element "memstore" to MemstoreStatement
        :return:
        """
        return MemstoreStatement(self.validate_attributes(MemstoreModel))
