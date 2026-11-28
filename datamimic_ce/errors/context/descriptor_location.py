# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from __future__ import annotations

from dataclasses import dataclass

from datamimic_ce.errors.context.descriptor_identity import (
    get_descriptor_name,
    get_include_chain,
    logical_descriptor_name,
)


@dataclass(frozen=True)
class DescriptorLocation:
    """Immutable parse-time location context for descriptor-backed user errors."""

    element_tag: str
    attribute: str | None = None
    descriptor_path: str | None = None
    line: int | None = None
    column: int | None = None
    include_chain: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        active = get_descriptor_name()
        name = logical_descriptor_name(self.descriptor_path or active)
        object.__setattr__(self, "descriptor_path", name)
        if not self.include_chain and name == active:
            object.__setattr__(self, "include_chain", get_include_chain())

    def format(self) -> str:
        """Render only truthful context currently available from the parser seam."""
        parts = [f"<{self.element_tag}>"]
        if self.attribute:
            parts.append(f"attribute '{self.attribute}'")
        if self.line is not None:
            parts.append(f"line {self.line}")
        if self.column is not None:
            parts.append(f"column {self.column}")
        if self.descriptor_path:
            parts.append(f"descriptor '{self.descriptor_path}'")
        return " in ".join(parts[:1]) + "".join(
            f" at {part}" if idx == 1 else f" in {part}" for idx, part in enumerate(parts[1:], start=1)
        )
