# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import os
import platform
import sys
import time
from contextlib import contextmanager
from typing import Literal

from datamimic_ce.logger import logger
from datamimic_ce.utils.version_util import get_datamimic_lib_version


def log_system_info():
    """Log system information."""
    logger.info("Starting DATAMIMIC Process")
    logger.info(f"DATAMIMIC CE lib version: {get_datamimic_lib_version('datamimic-ce')}")
    ee_lib_version = get_datamimic_lib_version("datamimic-ee")
    if ee_lib_version != "unknown":
        logger.info(f"DATAMIMIC EE lib version: {ee_lib_version}")
    logger.info(f"System name: {platform.system()}")
    logger.info(f"Process ID: {os.getpid()}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Number of CPU cores: {os.cpu_count()}")
    logger.info(f"CPU architecture: {platform.machine()}")


@contextmanager
def gen_timer(process: Literal["generate", "export", "process"], report_logging: bool, product_name: str):
    """
    Timer for generate and export process.

    :param process: Type of process ('generate', 'consume', 'process').
    :param report_logging: Whether to log the timing information.
    :param product_name: Name of the product being processed.
    :return: Context manager.
    """
    timer_result: dict = {}
    # Ignore timer if report_logging is False
    if not report_logging:
        yield timer_result
        return
    start_time = time.time()
    try:
        yield timer_result
    finally:
        records_count = timer_result.get("records_count", 0)
        end_time = time.time()
        elapsed_time = end_time - start_time
        # timer_result["elapsed_time"] = elapsed_time
        match process:
            case "generate":
                process_name = "Generating"
            case "export":
                process_name = "Exporting"
            case _:
                process_name = "Generating and exporting"
        logger.info(
            f"{process_name} {records_count:,} records '{product_name}' took {round(elapsed_time, 5)} seconds "
            f"({int(records_count / elapsed_time):,} records/second)"
            if elapsed_time > 0
            else "N/A records/second"
        )
