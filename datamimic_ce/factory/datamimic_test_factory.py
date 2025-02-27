# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.factory.factory_config import FactoryConfig
from datamimic_ce.logger import logger
from datamimic_ce.parsers.descriptor_parser import DescriptorParser
from datamimic_ce.statements.generate_statement import GenerateStatement
from datamimic_ce.statements.setup_statement import SetupStatement
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class DataMimicTestFactory:
    def __init__(self, xml_path: Path, entity_name: str):
        self._xml_path = xml_path
        self._entity_name = entity_name


    def create(self, custom_data: dict = {}):
        factory_config = FactoryConfig(self._entity_name, count=1, custom_data=custom_data)
        test_engine = DataMimicTest(self._xml_path.parent, self._xml_path.name, capture_test_result=True, factory_config=factory_config)
        test_engine.test_with_timer()
        result = test_engine.capture_result().get(self._entity_name)
        assert len(result) == 1  # Only one entity is generated
        result[0].update(custom_data)
        return result[0]

    def create_batch(self, count: int, custom_data: dict = {}):
        factory_config = FactoryConfig(self._entity_name, count=count, custom_data=custom_data)
        test_engine = DataMimicTest(self._xml_path.parent, self._xml_path.name, capture_test_result=True, factory_config=factory_config)
        test_engine.test_with_timer()
        result = test_engine.capture_result().get(self._entity_name)
        assert len(result) == count  # Only one entity is generated
        for entity in result:
            entity.update(custom_data)
        return result
