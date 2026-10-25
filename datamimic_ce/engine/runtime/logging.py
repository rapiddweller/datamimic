# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import logging
import os
import platform
import re
import sys
import time
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Literal

import psutil

from datamimic_ce.domains.api import get_datamimic_lib_version

# Every character str.splitlines() splits on, bar CR: a reader that splits lines that way must not see a new record.
_LINE_BREAKS = r"[\n\v\f\x1c\x1d\x1e\x85\u2028\u2029]"


class _SingleLineFormatter(logging.Formatter):
    """A record is one physical line: descriptor text may hold line breaks, and a continuation line that starts
    with a CONTROL marker would otherwise pass for a record of its own. Tracebacks are appended after the message
    and stay multi-line."""

    def formatMessage(self, record: logging.LogRecord) -> str:
        line = logging.Formatter.formatMessage(self, record)
        return re.sub(_LINE_BREAKS, r"\\n", re.sub(r"\r", r"\\r", line))


def setup_logger(logger_name: str, worker_name: str, level=logging.INFO):
    current_logger = logging.getLogger(logger_name)
    logging.addLevelName(logging.DEBUG, "DEBUG")
    logging.addLevelName(logging.INFO, "INFO ")
    logging.addLevelName(logging.WARNING, "WARN ")
    logging.addLevelName(logging.ERROR, "ERROR")
    logging.addLevelName(logging.CRITICAL, "CRTCL")

    # TODO: check if ray support this configuration with PR https://github.com/ray-project/ray/pull/48742
    if worker_name == "MAIN":
        formatter = _SingleLineFormatter(
            f"%(asctime)s | %(levelname)-5s | %(name)-9s | {worker_name}    | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S,%f"[:-3],
        )
    else:
        worker_proc_name, worker_id = worker_name.split("-")[0:2]
        formatter = _SingleLineFormatter(
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


logger = logging.getLogger("DATAMIMIC")


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


class _GenerationTimer(AbstractContextManager[dict[str, int]]):
    def __init__(self, process: Literal["generate", "export", "process"], report_logging: bool, product_name: str):
        self._process = process
        self._report_logging = report_logging
        self._product_name = product_name
        self._result: dict[str, int] = {}
        self._start_time = 0.0

    def __enter__(self) -> dict[str, int]:
        self._start_time = time.time()
        return self._result

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self._report_logging:
            return
        records_count = self._result.get("records_count", 0)
        elapsed_time = time.time() - self._start_time
        match self._process:
            case "generate":
                process_name = "Generating"
            case "export":
                process_name = "Export phase for"
            case _:
                process_name = "Processing"
        logger.info(
            f"{process_name} {records_count:,} records '{self._product_name}' took {round(elapsed_time, 5)} seconds "
            f"({int(records_count / elapsed_time):,} records/second)"
            if elapsed_time > 0
            else "N/A records/second"
        )


def gen_timer(
    process: Literal["generate", "export", "process"], report_logging: bool, product_name: str
) -> AbstractContextManager[dict[str, int]]:
    """Time operations without contextlib rewriting frozen domain exceptions."""
    return _GenerationTimer(process, report_logging, product_name)


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
