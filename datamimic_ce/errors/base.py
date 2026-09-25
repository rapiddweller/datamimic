from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainError(Exception):
    code: str
    message: str
    hint: str | None
    path: str
    request_hash: str
    details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
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
