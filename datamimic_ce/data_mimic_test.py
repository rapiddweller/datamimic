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
from datamimic_ce.interfaces.contracts import FactoryConfig, RunRequest, RunSession

logger = logging.getLogger("DATAMIMIC")


class DataMimicTest:
    def __init__(
        self,
        test_dir: Path,
        filename: str,
        capture_test_result: bool = False,
        factory_config: FactoryConfig | None = None,
    ):
        test_file_path = test_dir / filename
        self._capture_test_result = capture_test_result
        self._task_id = str(uuid.uuid4())
        self._session: RunSession = create_run_session(
            RunRequest(
                descriptor_path=test_file_path,
                task_id=self._task_id,
                test_mode=capture_test_result,
                factory_config=factory_config,
            )
        )

    @property
    def task_id(self):
        return self._task_id

    def test_with_timer(self):
        """
        Test with timer
        :return:
        """
        start_time = time.time()

        # Use default string instead of UUID4 for testing if not able get task_id from celery request
        self._session.execute()

        # Get the current time after the code execution
        end_time = time.time()
        # Calculate the elapsed time
        elapsed_time = end_time - start_time
        logger.info(f"The test took {elapsed_time} seconds to execute.")

    def capture_result(self):
        """
        Capture test data
        :return:
        """
        if self._capture_test_result:
            captured = self._session.capture_test_result()
            return captured.root if captured is not None else None
        else:
            raise ValueError("Capturing test result mode is currently disable")
