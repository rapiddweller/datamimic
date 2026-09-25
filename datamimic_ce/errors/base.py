from __future__ import annotations

from dataclasses import dataclass

from datamimic_ce.errors.codes import DomainErrorCode, ErrorCode


@dataclass(frozen=True)
class DomainError(Exception):
    code: DomainErrorCode | ErrorCode
    message: str
    hint: str | None
    path: str
    request_hash: str
    details: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code.value,
            "message": self.message,
            "path": self.path,
            "request_hash": self.request_hash,
        }
        if self.hint:
            payload["hint"] = self.hint
        if self.details is not None:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class InvalidLocaleError(ValueError, DomainError):
    """CE 5.0 aligns the Python locale error code and message with EE's E002 contract."""

    locale: str | None = None

    def __str__(self) -> str:
        return self.message
