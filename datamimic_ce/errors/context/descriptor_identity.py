# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import PurePosixPath, PureWindowsPath

_DESCRIPTOR_NAME: ContextVar[str | None] = ContextVar("dm_descriptor_name", default=None)


def get_descriptor_name() -> str | None:
    """Return the active descriptor name when in a descriptor scope."""
    return _DESCRIPTOR_NAME.get()


@contextmanager
def descriptor_scope(name: str | None) -> Iterator[None]:
    """Temporarily set the descriptor name for error context propagation."""
    token = _DESCRIPTOR_NAME.set(logical_descriptor_name(name))
    try:
        yield
    finally:
        _DESCRIPTOR_NAME.reset(token)


def logical_descriptor_name(name: str | None) -> str | None:
    if name is None:
        return None
    path = PureWindowsPath(name) if "\\" in name else PurePosixPath(name)
    return path.name if path.is_absolute() else name
