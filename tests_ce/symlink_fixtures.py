# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

from pathlib import Path

import pytest


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
