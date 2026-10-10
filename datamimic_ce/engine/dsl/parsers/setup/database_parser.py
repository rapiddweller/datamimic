# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path

from datamimic_ce.engine.dsl.model.setup.database_model import DatabaseModel
from datamimic_ce.engine.dsl.parsers.base.client_config import ConnectionProfileLoader, fulfill_credentials
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.setup.database_statement import DatabaseStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_DATABASE


class DatabaseParser(StatementParser):
    """
    Parse element "database" into DatabaseStatement
    """

    def __init__(
        self,
        element: XmlElement,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_DATABASE,
        )

    def parse(self, descriptor_dir: Path, *, profile_loader: ConnectionProfileLoader) -> DatabaseStatement:
        """
        Parse element "database" into DatabaseStatement
        :return:
        """
        db_credentials = fulfill_credentials(
            descriptor_dir=descriptor_dir,
            descriptor_attr=dict(self._element.attrib),
            env_props=self.properties,
            system_type="db",
            runtime_environment=self.runtime_environment,
            profile_loader=profile_loader,
        )
        return DatabaseStatement(self.validate_attributes(DatabaseModel, db_credentials))
