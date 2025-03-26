# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from pathlib import Path

from datamimic_ce.data_mimic_test import DataMimicTest
from datamimic_ce.factory.factory_config import FactoryConfig


class DataMimicTestFactory:
    def __init__(self, xml_path: Path | str, entity_name: str):
        self._xml_path = Path(xml_path)
        self._entity_name = entity_name

    def create(self, custom_data: dict | None = None):
        """
        Create a single entity
        :param custom_data: Custom data to be added to the entity
        :return: Created entity
        """
        # Create factory config
        factory_config = FactoryConfig(self._entity_name, count=1, custom_data=custom_data)

        # Create test engine with factory config
        test_engine = DataMimicTest(
            self._xml_path.parent,
            self._xml_path.name,
            capture_test_result=True,
            factory_config=factory_config,
        )

        # Execute test
        test_engine.test_with_timer()

        # Capture result
        result = test_engine.capture_result().get(self._entity_name)
        assert len(result) == 1  # Only one entity is generated

        # Update custom data if provided
        if custom_data is not None:
            result[0].update(custom_data)

        # Return the created entity
        return result[0]

    def create_batch(self, count: int, custom_data: dict | None = None):
        """
        Create a batch of entities
        :param count: Number of entities to create
        :param custom_data: Custom data to be added to the entities
        :return: List of created entities
        """
        # Create factory config
        factory_config = FactoryConfig(self._entity_name, count=count, custom_data=custom_data)

        # Create test engine with factory config
        test_engine = DataMimicTest(
            self._xml_path.parent,
            self._xml_path.name,
            capture_test_result=True,
            factory_config=factory_config,
        )

        # Execute test
        test_engine.test_with_timer()

        # Capture result
        result = test_engine.capture_result().get(self._entity_name)
        assert len(result) == count  # Only one entity is generated

        # Update custom data if provided
        if custom_data is not None:
            for entity in result:
                entity.update(custom_data)

        # Return the created entities
        return result
