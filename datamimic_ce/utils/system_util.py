# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import psutil

from datamimic_ce.logger import logger


def format_memory_size(size_in_mb: float) -> str:
    """Formats the memory size."""
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
