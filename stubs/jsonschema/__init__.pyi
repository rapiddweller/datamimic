from collections.abc import Iterable, Sequence
from typing import Protocol


class _ValidationPath(Protocol):
    def __lt__(self, other: _ValidationPath, /) -> bool: ...


class ValidationError:
    message: str
    absolute_path: Sequence[str | int]
    path: _ValidationPath


class Draft7Validator:
    def __init__(self, schema: object) -> None: ...

    def iter_errors(self, instance: object) -> Iterable[ValidationError]: ...
