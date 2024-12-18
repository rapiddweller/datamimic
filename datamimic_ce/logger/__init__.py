# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import logging
import multiprocessing
import os
import sys

from datamimic_ce.config import settings


def setup_logger(logger_name, task_id, level=logging.INFO):
    current_logger = logging.getLogger(logger_name)
    logging.addLevelName(logging.DEBUG, "DEBUG")
    logging.addLevelName(logging.INFO, "INFO ")
    logging.addLevelName(logging.WARNING, "WARN ")
    logging.addLevelName(logging.ERROR, "ERROR")
    logging.addLevelName(logging.CRITICAL, "CRTCL")

    get_current_process_name()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)-9s | %(processName)-10s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S,%f"[:-3],
    )

    # Avoid adding duplicate stream handlers
    if not any(isinstance(handler, logging.StreamHandler) for handler in current_logger.handlers):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        current_logger.setLevel(level)
        current_logger.addHandler(stream_handler)

    current_logger.propagate = False  # Avoid propagation to the parent logger


def get_current_process_name():
    # Get process information for logging purposes (e.g., process name) and WORKER should have WORKER-PID
    # current_process = multiprocessing.current_process()
    current_process = multiprocessing.current_process()
    pid = os.getpid()
    if current_process.name == "MainProcess":
        current_process.name = f"MAIN-{pid}"
    elif current_process.name.startswith("SpawnPoolWorker-") or current_process.name.startswith("ForkPoolWorker-"):
        current_process.name = f"WORK-{pid}"


logger = logging.getLogger(settings.DEFAULT_LOGGER)
