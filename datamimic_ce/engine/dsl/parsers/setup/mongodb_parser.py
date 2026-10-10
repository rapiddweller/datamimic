# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.engine.dsl.model.setup.mongodb_model import MongoDBModel
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader, fulfill_credentials
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.setup.mongodb_statement import MongoDBStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_MONGODB


class MongoDBParser(StatementParser):
    """
    Parse element "mongodb" into MongoDBStatement
    """

    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_MONGODB,
        )

    def parse(self, descriptor_dir: Path, *, profile_loader: ConnectionProfileLoader) -> MongoDBStatement:
        """
        Parse element "mongodb" into MongoDBStatement
        :return:
        """
        mongodb_attributes = fulfill_credentials(
            descriptor_dir=descriptor_dir,
            descriptor_attr=dict(self._element.attrib),
            env_props=self.properties,
            system_type="mongo",
            runtime_environment=self.runtime_environment,
            profile_loader=profile_loader,
        )

        return MongoDBStatement(
            model=self.validate_attributes(model=MongoDBModel, fulfilled_credentials=mongodb_attributes)
        )
