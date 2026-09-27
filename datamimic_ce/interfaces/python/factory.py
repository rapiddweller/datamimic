# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import logging
import time
import uuid
from pathlib import Path

from datamimic_ce.interfaces.api import create_run_session
from datamimic_ce.interfaces.contracts import FactoryConfig, RunRequest

logger = logging.getLogger("DATAMIMIC")


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
        test_engine = create_run_session(
            RunRequest(
                descriptor_path=self._xml_path,
                task_id=str(uuid.uuid4()),
                test_mode=True,
                factory_config=factory_config,
            )
        )

        # Execute test
        start_time = time.perf_counter()
        test_engine.execute()
        logger.info(f"The test took {time.perf_counter() - start_time} seconds to execute.")

        # Capture result
        capture = test_engine.capture_test_result()
        assert capture is not None
        result = capture.root.get(self._entity_name)
        assert result is not None
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
        test_engine = create_run_session(
            RunRequest(
                descriptor_path=self._xml_path,
                task_id=str(uuid.uuid4()),
                test_mode=True,
                factory_config=factory_config,
            )
        )

        # Execute test
        start_time = time.perf_counter()
        test_engine.execute()
        logger.info(f"The test took {time.perf_counter() - start_time} seconds to execute.")

        # Capture result
        capture = test_engine.capture_test_result()
        assert capture is not None
        result = capture.root.get(self._entity_name)
        assert result is not None
        assert len(result) == count  # Only one entity is generated

        # Update custom data if provided
        if custom_data is not None:
            for entity in result:
                entity.update(custom_data)

        # Return the created entities
        return result
