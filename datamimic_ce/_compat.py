"""Small standard-library compatibility shims for supported Python versions."""

from __future__ import annotations

from enum import Enum
from typing import NoReturn


class StrEnum(str, Enum):
    """Typed subset of :class:`enum.StrEnum` for explicit string values.

    Defining this consistently on every supported interpreter keeps static analysis
    independent from the configured Python target while preserving the runtime
    behavior used by DATAMIMIC's enums.
    """

    def __str__(self) -> str:
        return str(self.value)


def assert_never(value: NoReturn) -> NoReturn:
    """Python 3.10 equivalent of :func:`typing.assert_never`."""

    raise AssertionError(f"Expected code to be unreachable, received: {value!r}")


__all__ = ["StrEnum", "assert_never"]
