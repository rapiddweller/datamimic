# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_DATABASE
from datamimic_ce.model.database_model import DatabaseModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.database_statement import DatabaseStatement
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil


class DatabaseParser(StatementParser):
    """
    Parse element "database" into DatabaseStatement
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
            valid_element_tag=EL_DATABASE,
            class_factory_util=class_factory_util,
        )

    def parse(self, descriptor_dir: Path) -> DatabaseStatement:
        """
        Parse element "database" into DatabaseStatement
        :return:
        """
        from datamimic_ce.parsers.parser_util import ParserUtil

        db_credentials = ParserUtil.fulfill_credentials_v2(
            descriptor_dir=descriptor_dir,
            descriptor_attr=self._element.attrib,
            env_props=self.properties,
            system_type="db",
        )
        return DatabaseStatement(self.validate_attributes(DatabaseModel, db_credentials))
