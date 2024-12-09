# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


import time
import uuid
from pathlib import Path

from datamimic_ce.datamimic import DataMimic
from datamimic_ce.logger import logger


class DataMimicTest:
    def __init__(self, test_dir: Path, filename: str, capture_test_result: bool = False):
        test_file_path = test_dir / filename
        self._capture_test_result = capture_test_result
        self._task_id = str(uuid.uuid4())
        self._engine = DataMimic(
            descriptor_path=test_file_path,
            task_id=self._task_id,
            test_mode=capture_test_result,
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
        self._engine.parse_and_execute()

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
            return self._engine.capture_test_result()
        else:
            raise ValueError("Capturing test result mode is currently disable")
