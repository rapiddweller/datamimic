from pickle import Pickler as _Pickler, Unpickler as _Unpickler
from typing import BinaryIO, TypedDict


class _Settings(TypedDict):
    protocol: int
    byref: bool
    fmode: int
    recurse: bool
    ignore: bool


settings: _Settings


class Pickler(_Pickler):
    def __init__(
        self,
        file: BinaryIO,
        protocol: int | None = None,
        byref: bool | None = None,
        fmode: int | None = None,
        recurse: bool | None = None,
        **kwds: object,
    ) -> None: ...


class Unpickler(_Unpickler): ...


def dumps(obj: object) -> bytes: ...
def loads(data: bytes) -> dict[str, object]: ...
