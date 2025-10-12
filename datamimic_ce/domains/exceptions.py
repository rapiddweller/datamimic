from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DomainError(Exception):
    code: str
    message: str
    hint: str | None
    path: str
    request_hash: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        # mypy: Without an explicit annotation, this dict is inferred as dict[str, str].
        # We include optional structured details later, so keep value type as Any.
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "request_hash": self.request_hash,
        }
        if self.hint:
            payload["hint"] = self.hint
        if self.details is not None:
            payload["details"] = self.details
        return payload
