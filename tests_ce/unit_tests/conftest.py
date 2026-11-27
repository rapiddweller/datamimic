import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests_ce.symlink_fixtures import _probe_symlinks


@pytest.fixture
def require_symlinks(tmp_path: Path) -> None:
    """Skip only when Windows denies symlink creation; unexpected errors remain failures."""
    _probe_symlinks(tmp_path)


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
