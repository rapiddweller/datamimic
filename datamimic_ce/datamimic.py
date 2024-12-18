# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import argparse
import logging
import traceback
import uuid
from pathlib import Path

from datamimic_ce.config import settings
from datamimic_ce.exporters.test_result_exporter import TestResultExporter
from datamimic_ce.logger import logger, setup_logger
from datamimic_ce.parsers.descriptor_parser import DescriptorParser
from datamimic_ce.tasks.setup_task import SetupTask
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil
from datamimic_ce.utils.logging_util import log_system_info
from datamimic_ce.utils.system_util import log_memory_info

LOG_FILE = "datamimic.log"


class DataMimic:
    def __init__(
        self,
        descriptor_path: Path,
        task_id: str | None = None,
        platform_props: dict[str, str] | None = None,
        platform_configs: dict | None = None,
        test_mode: bool = False,
        args: argparse.Namespace | None = None,
    ):
        """
        Initialize DataMimic with descriptor_path.
        """
        # Set up logger
        log_level = getattr(logging, args.log_level.upper(), logging.INFO) if args else logging.INFO
        setup_logger(logger_name=settings.DEFAULT_LOGGER, task_id=task_id, level=log_level)

        self._task_id = task_id or uuid.uuid4().hex
        self._descriptor_path = descriptor_path
        self._platform_props = platform_props
        self._platform_configs = platform_configs
        self._test_mode = test_mode
        self._test_result_storage = TestResultExporter() if test_mode else None

        # Initialize logging
        log_system_info()
        log_memory_info(self._platform_configs)
        logger.info(f"Task ID: {self._task_id}")

        self._validate_descriptor_path()
        self._class_factory_util = ClassFactoryCEUtil()

    def _validate_descriptor_path(self):
        """Validates that the descriptor path is a valid file."""
        if not self._descriptor_path.is_file():
            logger.error(f"Invalid descriptor file path: {self._descriptor_path}")
            raise ValueError(f"Invalid file path: {self._descriptor_path}")

    def parse_and_execute(self) -> None:
        """Parse root XML descriptor file and execute."""
        try:
            root_stmt = DescriptorParser.parse(self._class_factory_util, self._descriptor_path, self._platform_props)
            setup_task = SetupTask(
                class_factory_util=self._class_factory_util,
                setup_stmt=root_stmt,
                memstore_manager=None,
                task_id=self._task_id,
                properties=self._platform_props,
                test_mode=self._test_mode,
                test_result_storage=self._test_result_storage,
                descriptor_dir=self._descriptor_path.parent,
            )
            setup_task.execute()
        except ValueError as e:
            logger.error(f"Value error: {e}")
            raise e
        except Exception as err:
            logger.exception("Error in DATAMIMIC process. Error message: {err}")
            traceback.print_exc()
            raise err

    def capture_test_result(self) -> dict | None:
        """Capture test result in test mode."""
        if self._test_mode and self._test_result_storage is not None:
            return self._test_result_storage.get_result()
        raise ValueError("Cannot capture test result in non-test mode") from None
