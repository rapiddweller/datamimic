# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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
