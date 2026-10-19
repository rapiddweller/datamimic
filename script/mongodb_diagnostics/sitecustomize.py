"""Opt-in driver metadata for the service CI, including spawned Python workers."""

import logging
import os
from pathlib import Path

directory = os.environ.get("DATAMIMIC_MONGODB_DIAGNOSTICS_DIR")
if directory:
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(destination / f"mongodb-driver-{os.getpid()}.log", mode="a", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s pid=%(process)d %(processName)s %(name)s %(message)s"))
    for name in ("pymongo.connection", "pymongo.serverSelection", "pymongo.topology"):
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
