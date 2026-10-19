# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""One private-process CE execution, using the existing engine capture core."""

from __future__ import annotations

import os
import pickle
import sys
import time
from pathlib import Path

from datamimic_ce.authoring.adapters.bounded_executor import _MAX_REPLY_BYTES
from datamimic_ce.authoring.adapters.dryrun import _run_engine_capture
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.engine.dsl.api import resource_reader_scope


def main() -> None:
    request_file, reply_file, root = map(Path, sys.argv[1:])
    request = BoundedExecutionRequest.model_validate_json(request_file.read_text(encoding="utf-8"))
    descriptor = request.descriptor_path
    workspace = AuthoringWorkspaceContext(root, descriptor)
    path = workspace.resolve_descriptor_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(request.xml, encoding="utf-8")
    os.chdir(root)
    with resource_reader_scope(workspace.read_resource_bytes):
        message = _run_engine_capture(
            path,
            request.max_count,
            request.allow_side_effects,
            request.smoke_export,
            profile_loader=workspace.load_connection_profile,
            environment_properties=dict(request.environment_properties),
            logical_descriptor_path=request.descriptor_path.as_posix(),
            workspace_root=workspace.root,
        )
    payload = pickle.dumps(message, protocol=pickle.HIGHEST_PROTOCOL)
    if len(payload) > _MAX_REPLY_BYTES:
        raise ValueError("bounded child evidence exceeds the transport limit")
    staging = reply_file.with_suffix(".tmp")
    staging.write_bytes(payload)
    staging.replace(reply_file)
    # Keep the tree leader alive until the parent has terminated all descendants (Windows taskkill).
    time.sleep(request.timeout_seconds + 5)


if __name__ == "__main__":
    main()
