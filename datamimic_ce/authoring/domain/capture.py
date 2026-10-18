# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Complete runtime captures; response samples never replace these rows."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, TypeAlias
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator
from typing_extensions import TypeAliasType

from .common import NonEmptyStrictStr, NonNegativeStrictInt, PositiveStrictInt

MAX_CAPTURE_DEPTH = 64
MAX_CAPTURE_ITEMS = 1_000_000


@dataclass(frozen=True)
class CapturedObjectId:
    """Passive BSON identity retained until an output boundary projects its text."""

    value: str

    def __post_init__(self) -> None:
        if (
            type(self.value) is not str
            or len(self.value) != 24
            or any(char not in "0123456789abcdef" for char in self.value)
        ):
            raise ValueError("captured ObjectId must be canonical lowercase hexadecimal")


CaptureValue: TypeAlias = (
    str
    | bool
    | int
    | float
    | Decimal
    | date
    | datetime
    | UUID
    | CapturedObjectId
    | None
    | dict[str, "CaptureValue"]
    | list["CaptureValue"]
    | tuple["CaptureValue", ...]
)
if not TYPE_CHECKING:
    # Pydantic needs a named recursive alias on Python 3.11.
    CaptureValue = TypeAliasType("CaptureValue", CaptureValue)


class CaptureStatus(StrEnum):
    """Runtime knowledge about whether a bounded product capture is complete."""

    COMPLETE = "complete"
    CAPPED = "capped"
    EXHAUSTED = "exhausted"
    UNKNOWN = "unknown"


class ProductCaptureEvidence(BaseModel):
    """Typed runtime evidence for one captured product."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    status: CaptureStatus
    requested: NonNegativeStrictInt | None
    observed: NonNegativeStrictInt
    limit: PositiveStrictInt
    reason: NonEmptyStrictStr

    @property
    def complete(self) -> bool:
        """Whether runtime evidence proves the bounded capture is complete."""

        return self.status in (CaptureStatus.COMPLETE, CaptureStatus.EXHAUSTED)

    @model_validator(mode="after")
    def _consistent_counts(self) -> ProductCaptureEvidence:
        if self.observed > self.limit:
            raise ValueError("observed must not exceed limit")
        if self.requested is not None and self.status is CaptureStatus.COMPLETE and self.observed != self.requested:
            raise ValueError("complete capture must observe the requested count")
        if self.status is CaptureStatus.CAPPED and self.observed != self.limit:
            raise ValueError("capped capture must observe its limit")
        return self


@dataclass(frozen=True)
class CapturedProduct:
    """All bounded rows captured for one runtime product before projection."""

    name: str
    rows: tuple[CaptureValue, ...]
    capture: ProductCaptureEvidence | None = None


@dataclass(frozen=True)
class CapturedProducts:
    """Internal acceptance input; unlike ``ProductResult`` this is never sampled."""

    products: tuple[CapturedProduct, ...]
    max_count: int

    def get(self, name: str) -> CapturedProduct | None:
        return next((product for product in self.products if product.name == name), None)


@dataclass(frozen=True)
class SmokeExportCapture:
    """Typed internal facts from smoke-export execution, without public policy."""

    requested: bool
    applicable_exporters: int
    attempted_exporters: int
    failed_exporters: int

    @classmethod
    def not_requested(cls) -> SmokeExportCapture:
        return cls(
            requested=False,
            applicable_exporters=0,
            attempted_exporters=0,
            failed_exporters=0,
        )


def validate_capture_values(value: object) -> None:
    """Reject cyclic, oversized or executable values before any capture consumer."""
    stack: list[tuple[object, int, frozenset[int]]] = [(value, 0, frozenset())]
    remaining = MAX_CAPTURE_ITEMS
    while stack:
        current, depth, ancestors = stack.pop()
        remaining -= 1
        if remaining < 0 or depth > MAX_CAPTURE_DEPTH:
            raise ValueError("capture exceeds its item or depth budget")
        if type(current) is CapturedObjectId:
            if current.__dict__.keys() != {"value"}:
                raise ValueError("captured ObjectId contains noncanonical state")
            CapturedObjectId(value=current.value)
            continue
        if current is None or isinstance(current, str | bool | date | datetime | UUID):
            continue
        if isinstance(current, int):
            if current.bit_length() > 14_000:
                raise ValueError("capture integer exceeds JSON serialization limits")
            continue
        if isinstance(current, float) and math.isfinite(current):
            continue
        if isinstance(current, Decimal) and current.is_finite():
            continue
        if isinstance(current, dict | list | tuple):
            identity = id(current)
            if identity in ancestors:
                raise ValueError("capture contains a cyclic container")
            values: Iterable[object]
            if isinstance(current, dict):
                if not all(isinstance(key, str) for key in current):
                    raise ValueError("capture object keys must be strings")
                values = current.values()
            else:
                values = current
            if len(stack) + len(current) > remaining:
                raise ValueError("capture exceeds its item budget")
            lineage = ancestors | {identity}
            stack.extend((item, depth + 1, lineage) for item in values)
            continue
        raise ValueError("capture contains a non-finite or unsupported passive value")
