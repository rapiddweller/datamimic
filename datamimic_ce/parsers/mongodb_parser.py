# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_MONGODB
from datamimic_ce.model.mongodb_model import MongoDBModel
from datamimic_ce.parsers.parser_util import ParserUtil
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.mongodb_statement import MongoDBStatement


class MongoDBParser(StatementParser):
    """
    Parse element "mongodb" into MongoDBStatement
    """

    def __init__(
        self,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_MONGODB,
        )

    def parse(self, descriptor_dir: Path) -> MongoDBStatement:
        """
        Parse element "mongodb" into MongoDBStatement
        :return:
        """
        mongodb_attributes = ParserUtil.fulfill_credentials(
            descriptor_dir=descriptor_dir,
            descriptor_attr=self._element.attrib,
            env_props=self.properties,
            system_type="mongo",
        )

        return MongoDBStatement(
            model=self.validate_attributes(model=MongoDBModel, fulfilled_credentials=mongodb_attributes)
        )
