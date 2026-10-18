# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from __future__ import annotations

from dataclasses import dataclass

from datamimic_ce.errors.codes import IssueCode, IssueSeverity


@dataclass(frozen=True)
class IssueDefinition:
    code: IssueCode
    name: str
    title: str
    template: str
    cause: str
    resolution: str
    guidance: str | None = None
    severity: IssueSeverity = IssueSeverity.ERROR  # WARNING issues are logged-once (task_warning), never raised

    def __post_init__(self) -> None:
        if self.code.value.startswith("W") != (self.severity is IssueSeverity.WARNING):
            raise ValueError(f"Issue {self.code} has inconsistent severity {self.severity}.")
