# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""One private-process CE execution, using the existing engine capture core."""

from __future__ import annotations

import os
import pickle
import sys
import tempfile
import time
from pathlib import Path

from datamimic_ce.authoring.adapters.bounded_executor import _MAX_REPLY_BYTES
from datamimic_ce.authoring.adapters.dryrun import _run_engine_capture
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.engine.dsl.api import resource_reader_scope

# Audit events that start a process; refused in every bounded run without side effects.
_PROCESS_EVENTS = frozenset({"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork"})
# Audit events whose first two arguments name the paths they change.
_PATH_EVENTS = frozenset(
    {
        "os.remove",
        "os.rename",
        "os.mkdir",
        "os.rmdir",
        "os.truncate",
        "os.chmod",
        "os.chown",
        "os.link",
        "os.symlink",
        "os.utime",
        "shutil.rmtree",
        "shutil.copyfile",
        "shutil.copytree",
        "shutil.move",
    }
)
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


def _contain(private_root: Path, workspace: Path) -> None:
    """Refuse writes outside ``private_root``, writes to files the workspace snapshot already holds, and new
    processes for the rest of this child process. Snapshot files are what the run was checked against: a
    library must not replace a later, already-checked library (#360) or a resource the proof reads.

    The engine itself writes only below the temp directory, which moves into ``private_root``. An audit
    hook cannot be removed once installed; native code outside the audited calls is not covered. The refusal
    is a plain PermissionError because the parent unpickles only listed exception types.
    """
    allowed = os.path.normcase(os.path.realpath(private_root))
    snapshot = frozenset(
        os.path.normcase(os.path.realpath(os.path.join(directory, name)))
        for directory, _, names in os.walk(workspace)
        for name in names
    )
    temporary = private_root / "tmp"
    os.makedirs(temporary, exist_ok=True)
    tempfile.tempdir = str(temporary)
    os.environ["TMPDIR"] = os.environ["TEMP"] = os.environ["TMP"] = str(temporary)

    def contained(path: str | bytes | os.PathLike[str]) -> bool:
        target = os.path.normcase(os.path.realpath(os.fsdecode(path)))
        if target == os.path.normcase(os.devnull):
            return True
        return target[: len(allowed) + 1] == allowed + os.sep and target not in snapshot

    def hook(event: str, args: tuple[object, ...]) -> None:
        if event in _PROCESS_EVENTS:
            raise PermissionError("Bounded execution cannot start a process")
        if event == "open":
            path, mode, flags = args
            writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or (
                isinstance(flags, int) and bool(flags & _WRITE_FLAGS)
            )
            # An integer path is a file descriptor, opened and checked before.
            if writing and isinstance(path, (str, bytes, os.PathLike)) and not contained(path):
                raise PermissionError("Bounded execution may write only new files inside its private workspace")
        elif event in _PATH_EVENTS and not all(
            contained(path) for path in args[:2] if isinstance(path, (str, bytes, os.PathLike))
        ):
            raise PermissionError("Bounded execution may write only new files inside its private workspace")

    sys.addaudithook(hook)


def main() -> None:
    request_file, reply_file, root = map(Path, sys.argv[1:])
    request = BoundedExecutionRequest.model_validate_json(request_file.read_text(encoding="utf-8"))
    descriptor = request.descriptor_path
    workspace = AuthoringWorkspaceContext(root, descriptor)
    path = workspace.resolve_descriptor_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(request.xml, encoding="utf-8")
    os.chdir(root)
    if not request.allow_side_effects:
        _contain(reply_file.parent, root)
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
