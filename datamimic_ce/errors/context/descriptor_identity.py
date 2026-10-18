# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from __future__ import annotations

from contextlib import AbstractContextManager
from contextvars import ContextVar, Token
from pathlib import PurePosixPath, PureWindowsPath
from types import TracebackType

_DESCRIPTOR_NAME: ContextVar[str | None] = ContextVar("dm_descriptor_name", default=None)


def get_descriptor_name() -> str | None:
    """Return the active descriptor name when in a descriptor scope."""
    return _DESCRIPTOR_NAME.get()


class _DescriptorScope(AbstractContextManager[None]):
    def __init__(self, name: str | None) -> None:
        self._name = logical_descriptor_name(name)
        self._token: Token[str | None] | None = None

    def __enter__(self) -> None:
        self._token = _DESCRIPTOR_NAME.set(self._name)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._token is not None:
            _DESCRIPTOR_NAME.reset(self._token)
            self._token = None


def descriptor_scope(name: str | None) -> AbstractContextManager[None]:
    """Reset descriptor context without contextlib rewriting frozen exceptions."""
    return _DescriptorScope(name)


def logical_descriptor_name(name: str | None) -> str | None:
    if name is None:
        return None
    path = PureWindowsPath(name) if "\\" in name else PurePosixPath(name)
    return path.name if path.is_absolute() else name
