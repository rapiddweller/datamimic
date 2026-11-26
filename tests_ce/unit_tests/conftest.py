import logging
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def require_symlinks(tmp_path: Path) -> None:
    """Skip only when Windows denies symlink creation; unexpected errors remain failures."""
    _probe_symlinks(tmp_path)


def _probe_symlinks(tmp_path: Path) -> None:
    link = tmp_path / "symlink-capability-probe"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except OSError as error:
        if getattr(error, "winerror", None) == 1314:
            pytest.skip("Creating symlinks requires Windows Developer Mode or the symlink privilege")
        raise
    else:
        link.unlink()


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
