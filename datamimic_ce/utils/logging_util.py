# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import os
import platform
import sys

from datamimic_ce.logger import logger
from datamimic_ce.utils.version_util import get_datamimic_lib_version


def log_system_info():
    """Log system information."""
    logger.info("Starting DATAMIMIC Process")
    logger.info(f"DATAMIMIC lib version: {get_datamimic_lib_version()}")
    logger.info(f"System name: {platform.system()}")
    logger.info(f"Process ID: {os.getpid()}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Platform: {sys.platform}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Number of CPU cores: {os.cpu_count()}")
    logger.info(f"CPU architecture: {platform.machine()}")
