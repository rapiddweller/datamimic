# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Construct the CE adapters only when an application is explicitly requested."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from datamimic_ce.authoring.domain.requests import DEFAULT_AUTHORING_DESCRIPTOR_PATH

if TYPE_CHECKING:
    from datamimic_ce.authoring.application.app import AuthoringApplication


def create_authoring_application(
    workspace_root: Path | None = None,
    descriptor_path: PurePosixPath = DEFAULT_AUTHORING_DESCRIPTOR_PATH,
) -> AuthoringApplication:
    from datamimic_ce.authoring.adapters.bounded_execution_policy import CeBoundedExecutionPolicy
    from datamimic_ce.authoring.adapters.bounded_executor import CeBoundedExecutor
    from datamimic_ce.authoring.adapters.catalog import CeDslCatalog
    from datamimic_ce.authoring.adapters.dm_json_codec import CeDmJsonCodec
    from datamimic_ce.authoring.adapters.validator import CeDescriptorValidator
    from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
    from datamimic_ce.authoring.application.app import AuthoringApplication

    workspace = AuthoringWorkspaceContext(workspace_root if workspace_root is not None else Path.cwd(), descriptor_path)

    codec = CeDmJsonCodec()
    return AuthoringApplication(
        catalog=CeDslCatalog(codec),
        validator=CeDescriptorValidator(workspace, profile_loader=workspace.load_connection_profile),
        executor=CeBoundedExecutor(workspace),
        descriptor_contract=codec,
        bounded_execution_policy=CeBoundedExecutionPolicy(),
        files=workspace,
    )
