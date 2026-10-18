# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Pure element content and bounded-execution vocabulary."""

from dataclasses import dataclass
from enum import StrEnum


class ElementContentModeKind(StrEnum):
    TEXT = "text"
    INLINE = "inline"
    URI = "uri"
    SCRIPT = "script"


@dataclass(frozen=True)
class ElementContentMode:
    kind: ElementContentModeKind
    required_attributes: tuple[str, ...] = ()


class BoundedExecutionStrategy(StrEnum):
    COUNTED = "counted"
    CONTAINER = "container"
    UNSUPPORTED = "unsupported"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class BoundedExecutionProfile:
    strategy: BoundedExecutionStrategy = BoundedExecutionStrategy.UNSUPPORTED
    count_attributes: tuple[str, ...] = ()
    source_attribute: str | None = None
    dependency_attribute: str | None = None
