import logging
from collections.abc import Iterator

import pytest


@pytest.fixture
def dm_caplog(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    # The DATAMIMIC logger may have propagate=False, so caplog must be attached to it directly.
    logger = logging.getLogger("DATAMIMIC")
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="DATAMIMIC"):
            yield caplog
    finally:
        logger.removeHandler(caplog.handler)
