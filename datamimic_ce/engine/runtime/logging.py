# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import logging
import os
import platform
import sys
import time
from contextlib import contextmanager
from typing import Literal

import psutil

from datamimic_ce.domains.determinism import get_datamimic_lib_version
from datamimic_ce.engine.runtime.config import settings


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
        # stderr, not stdout: logs must never interleave with data on stdout —
        # a stdio MCP transport owns stdout for JSON-RPC frames
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        current_logger.setLevel(level)
        current_logger.addHandler(stream_handler)

    current_logger.propagate = False  # Avoid propagation to the parent logger


logger = logging.getLogger(settings.DEFAULT_LOGGER)


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
    """Time a generate, export, or process operation."""
    timer_result: dict = {}
    if not report_logging:
        yield timer_result
        return
    start_time = time.time()
    try:
        yield timer_result
    finally:
        records_count = timer_result.get("records_count", 0)
        elapsed_time = time.time() - start_time
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


def format_memory_size(size_in_mb: float) -> str:
    """Format a memory size."""
    return f"{size_in_mb / 1024:.2f} GB" if size_in_mb >= 1024 else f"{size_in_mb:.2f} MB"


def log_memory_info(platform_configs: dict | None = None):
    """Log system memory information."""
    total_ram_mb = psutil.virtual_memory().total / (1024.0**2)
    logger.info(f"RAM size: {format_memory_size(total_ram_mb)}")

    if platform_configs:
        memory_limit_mb = platform_configs.get("memory_limit_mb", 0)
        if memory_limit_mb:
            logger.info(f"Limit memory usage: {format_memory_size(memory_limit_mb)}")
        else:
            logger.info("Limit memory usage: None")
