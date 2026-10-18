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
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from .common import NonEmptyStrictStr, NonNegativeStrictInt, PositiveStrictInt


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
    rows: tuple[object, ...]
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
    remaining = 1_000_000
    while stack:
        current, depth, ancestors = stack.pop()
        remaining -= 1
        if remaining < 0 or depth > 64:
            raise ValueError("capture exceeds its item or depth budget")
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
