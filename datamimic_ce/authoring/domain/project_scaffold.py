# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""A starter project as plain files, ready to write into an empty directory."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from datamimic_ce.authoring.domain.common import validate_workspace_descriptor_path
from datamimic_ce.authoring.domain.requests import PROJECT_ACCEPTANCE_PATH, PROJECT_ENTRY_PATH, BuildRequestV5


class ProjectPattern(StrEnum):
    """Starter projects that Build proves as written. CE ships one."""

    FLAT = "flat"


@dataclass(frozen=True, slots=True)
class ProjectScaffoldFile:
    path: PurePosixPath
    content: str

    def __post_init__(self) -> None:
        validate_workspace_descriptor_path(self.path)


@dataclass(frozen=True, slots=True)
class ProjectScaffold:
    pattern: ProjectPattern
    files: tuple[ProjectScaffoldFile, ...]

    @classmethod
    def from_starter(
        cls,
        pattern: ProjectPattern,
        entry_xml: str,
        acceptance: BuildRequestV5,
        project_files: tuple[ProjectScaffoldFile, ...] = (),
    ) -> ProjectScaffold:
        """Write the acceptance without its defaults, so that an agent edits only what matters."""
        unset = BuildRequestV5()
        payload: dict[str, object] = acceptance.taught_form("json")
        defaults: dict[str, object] = unset.taught_form("json")
        kept = {name: value for name, value in payload.items() if name == "version" or value != defaults.get(name)}
        return ProjectScaffold(
            pattern=pattern,
            files=(
                ProjectScaffoldFile(PROJECT_ENTRY_PATH, f"{entry_xml}\n"),
                ProjectScaffoldFile(PROJECT_ACCEPTANCE_PATH, f"{json.dumps(kept, indent=2)}\n"),
                *project_files,
            ),
        )
