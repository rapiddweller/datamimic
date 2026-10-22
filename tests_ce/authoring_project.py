# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Write a one-entry project and Build it, the way an agent does: files first, then Build the directory."""

from pathlib import Path

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ACCEPTANCE_PATH,
    PROJECT_ENTRY_PATH,
    BuildRequestV5,
    BuildResult,
)


def write_project(root: Path, entry: DmJsonDocumentV1 | str, **acceptance: object) -> Path:
    """``entry`` is the datamimic.xml text, or a DM JSON document compiled to it; ``acceptance`` holds the
    BuildRequestV5 fields written to acceptance/build.json."""
    xml = entry if isinstance(entry, str) else CeDmJsonCodec().compile(entry).xml
    (root / PROJECT_ENTRY_PATH).write_text(xml, encoding="utf-8")
    path = root / PROJECT_ACCEPTANCE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(BuildRequestV5.model_validate(acceptance).model_dump_json(), encoding="utf-8")
    return root


def build_project(root: Path, entry: DmJsonDocumentV1 | str, **acceptance: object) -> BuildResult:
    write_project(root, entry, **acceptance)
    return create_authoring_application(root, descriptor_path=PROJECT_ENTRY_PATH).build()
