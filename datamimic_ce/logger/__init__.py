# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import logging
import sys

from datamimic_ce.config import settings


def setup_logger(logger_name: str, worker_name: str, level=logging.INFO):
    current_logger = logging.getLogger(logger_name)
    logging.addLevelName(logging.DEBUG, "DEBUG")
    logging.addLevelName(logging.INFO, "INFO ")
    logging.addLevelName(logging.WARNING, "WARN ")
    logging.addLevelName(logging.ERROR, "ERROR")
    logging.addLevelName(logging.CRITICAL, "CRTCL")

    # TODO: check if ray support this configuration with PR https://github.com/ray-project/ray/pull/48742
    if worker_name == "MAIN":
        formatter = logging.Formatter(
            f"%(asctime)s | %(levelname)-5s | %(name)-9s | {worker_name}    | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S,%f"[:-3],
        )
    else:
        worker_proc_name, worker_id = worker_name.split("-")[0:2]
        formatter = logging.Formatter(
            f"%(asctime)s | %(levelname)-5s | %(name)-9s | {worker_proc_name}-{worker_id.zfill(2)} | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S,%f"[:-3],
        )

    # Avoid adding duplicate stream handlers
    if not any(isinstance(handler, logging.StreamHandler) for handler in current_logger.handlers):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        current_logger.setLevel(level)
        current_logger.addHandler(stream_handler)

    current_logger.propagate = False  # Avoid propagation to the parent logger


logger = logging.getLogger(settings.DEFAULT_LOGGER)
