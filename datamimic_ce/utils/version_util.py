# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import importlib.metadata
from importlib.resources import files

from datamimic_ce.logger import logger


def get_datamimic_lib_version() -> str | None:
    """Get DataMimic library version."""
    try:
        return importlib.metadata.version("datamimic-ce")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def get_last_commit_info() -> str | None:
    """Get last commit information from metadata.txt."""
    try:
        metadata_path = files("datamimic_ce").joinpath("metadata.txt")
        with metadata_path.open("r", encoding="utf-8") as file:
            metadata = dict(line.strip().split("=", 1) for line in file)
            return metadata.get("last_commit_time")
    except FileNotFoundError:
        logger.warning("metadata.txt not found. Last commit info unavailable.")
        return None
    except KeyError as e:
        logger.error(f"Key error in metadata.txt: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to get last commit info: {e}")
        return None
