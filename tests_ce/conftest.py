# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


import subprocess
import time

import pytest
import ray

from datamimic_ce.config import settings
from datamimic_ce.logger import logger


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


@pytest.fixture(scope="session")
def ray_session():
    ray.init()
    yield None
    ray.shutdown()
