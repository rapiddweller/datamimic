# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import logging
import multiprocessing
import os
import sys
from datetime import datetime

from datamimic_ce.config import settings


class CustomLogFormatter(logging.Formatter):
    def format(self, record):
        log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
        total_width = 7  # Total available width for the log level and surrounding space
        log_level = record.levelname
        centered_log_level = f"{log_level:^{total_width}}"  # Center the log level in the fixed-width space
        logger_name = f"{record.name:<9}"
        message = f"{log_time} | {centered_log_level} | {logger_name} | {record.getMessage()}"

        return message


def setup_logger(logger_name, task_id, level=logging.INFO):
    l = logging.getLogger(logger_name)
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

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    if not l.handlers:  # Avoid adding duplicate handlers
        l.setLevel(level)
        if settings.RUNTIME_ENVIRONMENT in ["development", "production"]:
            l.addHandler(stream_handler)
        else:
            l.addHandler(stream_handler)

    l.propagate = False  # Avoid propagation to the parent logger


def shutdown_logger(logger_name):
    l = logging.getLogger(logger_name)
    for handler in l.handlers:
        handler.close()
        l.removeHandler(handler)


def get_current_process_name():
    # Get process information for logging purposes (e.g., process name) and WORKER should have WORKER-PID    current_process = multiprocessing.current_process()
    current_process = multiprocessing.current_process()
    pid = os.getpid()
    if current_process.name == "MainProcess":
        current_process.name = f"MAIN-{pid}"
    elif current_process.name.startswith("SpawnPoolWorker-") or current_process.name.startswith("ForkPoolWorker-"):
        current_process.name = f"WORK-{pid}"


logger = logging.getLogger(settings.DEFAULT_LOGGER)
