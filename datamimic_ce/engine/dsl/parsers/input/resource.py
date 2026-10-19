"""Context-local input reads; normal runtime keeps its filesystem behavior."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import TypeAlias

ResourceReader: TypeAlias = Callable[[Path], bytes]
_READER: ContextVar[ResourceReader | None] = ContextVar("dsl_resource_reader", default=None)


def read_resource_bytes(path: Path) -> bytes:
    reader = _READER.get()
    return path.read_bytes() if reader is None else reader(path)


def resource_reader_active() -> bool:
    return _READER.get() is not None


@contextmanager
def resource_reader_scope(reader: ResourceReader) -> Iterator[None]:
    token = _READER.set(reader)
    try:
        yield
    finally:
        _READER.reset(token)
