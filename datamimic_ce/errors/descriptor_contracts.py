# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from __future__ import annotations

from typing import Protocol, runtime_checkable

# WHY: this contract is consumer-owned and satisfied structurally by runtime implementations.
# It must not import implementors, and implementors must not import it unless type-checking truly requires it.


@runtime_checkable
class DescriptorRootLike(Protocol):
    """Leaf contract for objects that may expose a descriptor name."""

    @property
    def descriptor_name(self) -> str | None:
        """Read-only descriptor name exposed by runtime roots."""


@runtime_checkable
class DescriptorCarrierLike(Protocol):
    """Leaf contract for objects that may expose descriptor information directly or via a root."""

    @property
    def root(self) -> DescriptorRootLike | None:
        """Read-only root reference exposed by runtime contexts."""
