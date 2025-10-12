# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

# WHY: Remove Ray-specific env var since Ray is optional and not used in tests.

# WHY: Ray is optional now. Remove hard dependency from tests.

from datamimic_ce.config import settings
from datamimic_ce.logger import logger

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

@pytest.fixture
def mysql_services():
    try:
        if settings.RUNTIME_ENVIRONMENT == "production":
            logger.info("Production Environment detected, no need to manually activate my sql services")
            yield None
            return
        else:
            # Run MySQL container
            subprocess.run(
                [
                    "docker",
                    "restart",
                    "mysql-local",
                ]
            )

            # Wait for MySQL to start
            time.sleep(5)

            yield

            # Tear down: Stop the container
            subprocess.run(
                [
                    "docker",
                    "stop",
                    "mysql-local",
                ]
            )

    except FileNotFoundError as e:
        logger.error("Failed to run cli command to start my sql, please double check docker config and images")
        raise e
    except Exception as e:
        raise e


# Removed unused ray_session fixture: tests do not require Ray.
