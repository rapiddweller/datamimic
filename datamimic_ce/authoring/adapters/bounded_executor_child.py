# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""One private-process CE execution, using the existing engine capture core."""

from __future__ import annotations

import dataclasses
import os
import pickle
import sys
import tempfile
import time
from pathlib import Path

from datamimic_ce.authoring.adapters.bounded_executor import _MAX_REPLY_BYTES
from datamimic_ce.authoring.adapters.dryrun import _run_engine_capture, _WorkerFailure, _WorkerSuccess
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest
from datamimic_ce.engine.dsl.api import resource_reader_scope

# Audit events that start a process; refused in every bounded run without side effects.
_PROCESS_EVENTS = frozenset(
    {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty", "os.startfile"}
)
# Audit events whose first two arguments name the paths they change, with the argument positions that carry dir_fd
# (-1 or None when absent); () marks events without one. CPython 3.11-3.13 raises no event for os.mkfifo or os.mknod,
# so _contain replaces both.
_PATH_EVENTS: dict[str, tuple[int, ...]] = {
    "os.remove": (1,),
    "os.rmdir": (1,),
    "shutil.rmtree": (1,),
    "os.mkdir": (2,),
    "os.chmod": (2,),
    "os.symlink": (2,),
    "os.rename": (2, 3),
    "os.link": (2, 3),
    "os.utime": (3,),
    "os.chown": (3,),
    "os.truncate": (),
    "os.chflags": (),
    "os.setxattr": (),
    "os.removexattr": (),
    "shutil.copyfile": (),
    "shutil.copytree": (),
    "shutil.move": (),
}
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


_FsPath = str | bytes | os.PathLike[str] | os.PathLike[bytes]


# os.mkfifo and os.mknod raise no audit event; in the contained child they are replaced by these refusals.
def _refuse_mkfifo(path: _FsPath, mode: int = 0o666, *, dir_fd: int | None = None) -> None:
    raise PermissionError("Bounded execution may write only new files inside its private workspace")


def _refuse_mknod(path: _FsPath, mode: int = 0o600, device: int = 0, *, dir_fd: int | None = None) -> None:
    raise PermissionError("Bounded execution may write only new files inside its private workspace")


def _contain(private_root: Path, workspace: Path, transport: tuple[Path, ...]) -> tuple[set[str], set[str]]:
    """Refuse writes outside ``private_root``, writes to files the workspace snapshot already holds, and new
    processes for the rest of this child process. Snapshot files are what the run was checked against: a
    library must not replace a later, already-checked library (#360) or a resource the proof reads. The
    ``transport`` files stay refused while the returned set holds them; the child clears it to write its reply,
    so the run cannot forge that reply. The second returned set collects the snapshot files the run opens for
    reading, as workspace-relative POSIX paths: the files its proof depends on.

    The engine itself writes only below the temp directory, which moves into ``private_root``. An audit
    hook cannot be removed once installed; native code outside the audited calls is not covered. The refusal
    is a plain PermissionError because the parent unpickles only listed exception types.
    """
    allowed = os.path.normcase(os.path.realpath(private_root))
    # Directories too: renaming one away and back would otherwise rewrite its files unseen.
    snapshot = frozenset(
        os.path.normcase(os.path.realpath(os.path.join(directory, name)))
        for directory, directories, names in os.walk(workspace)
        for name in (*directories, *names, "")
    )
    workspace_root = os.path.realpath(workspace)
    files = frozenset(
        os.path.normcase(os.path.realpath(os.path.join(directory, name)))
        for directory, _, names in os.walk(workspace)
        for name in names
    )
    read: set[str] = set()
    reply = {os.path.normcase(os.path.realpath(path)) for path in transport}
    # Windows resolves "nul" to "\\.\nul", so both spellings name the null device.
    null_device = {os.path.normcase(os.devnull), os.path.normcase(os.path.realpath(os.devnull))}
    temporary = private_root / "tmp"
    os.makedirs(temporary, exist_ok=True)
    # Python's tempfile is the engine's only temp writer; processes are refused and C code is not audited.
    tempfile.tempdir = str(temporary)

    def contained(path: str | bytes | os.PathLike[str]) -> bool:
        target = os.path.normcase(os.path.realpath(os.fsdecode(path)))
        return target[: len(allowed) + 1] == allowed + os.sep and target not in snapshot and target not in reply

    def hook(event: str, args: tuple[object, ...]) -> None:
        if event in _PROCESS_EVENTS:
            raise PermissionError("Bounded execution cannot start a process")
        if event == "open":
            path, mode, flags = args
            writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or (
                isinstance(flags, int) and bool(flags & _WRITE_FLAGS)
            )
            # An integer path is a file descriptor, opened and checked before. os.open (mode None) reports no
            # dir_fd, so a relative os.open write may land anywhere; the engine opens absolute paths only.
            # Writing to the null device is the one write outside the root the engine needs; only open gets it.
            if (
                writing
                and isinstance(path, (str, bytes, os.PathLike))
                and os.path.normcase(os.path.realpath(os.fsdecode(path))) not in null_device
                and (not contained(path) or (mode is None and not os.path.isabs(os.fsdecode(path))))
            ):
                raise PermissionError("Bounded execution may write only new files inside its private workspace")
            if not writing and isinstance(path, (str, bytes, os.PathLike)):
                real = os.path.realpath(os.fsdecode(path))
                if os.path.normcase(real) in files:
                    read.add(Path(os.path.relpath(real, workspace_root)).as_posix())
        elif event in _PATH_EVENTS:
            # Limit: shutil.rmtree of a non-empty relative tree stays refused; its inner events carry a real fd,
            # which looks like a caller's dir_fd.
            carries_dir_fd = any(isinstance(value := args[i], int) and value >= 0 for i in _PATH_EVENTS[event])
            # A file-descriptor form (os.chmod(fd), os.utime(fd)) names no path to check, so it is refused.
            if isinstance(args[0], int):
                raise PermissionError("Bounded execution may write only new files inside its private workspace")
            for path in args[:2]:
                # A relative path beside a real dir_fd resolves against a directory the event does not name.
                if isinstance(path, (str, bytes, os.PathLike)) and (
                    not contained(path) or (carries_dir_fd and not os.path.isabs(os.fsdecode(path)))
                ):
                    raise PermissionError("Bounded execution may write only new files inside its private workspace")
        elif event == "socket.bind":
            address = args[1]
            # Every non-tuple address is an AF_UNIX path. CPython also takes any buffer there; it cannot be read as a
            # path here, so it is refused like every other path outside the root.
            if not isinstance(address, tuple) and (
                not isinstance(address, (str, bytes))
                # A leading NUL names a Linux abstract socket, which creates no inode (not tested on Linux).
                or (os.fsdecode(address)[:1] != "\0" and not contained(address))
            ):
                raise PermissionError("Bounded execution may write only new files inside its private workspace")

    sys.addaudithook(hook)
    if os.name == "posix":
        os.mkfifo = _refuse_mkfifo
        os.mknod = _refuse_mknod
    return reply, read


def main() -> None:
    request_file, reply_file, root = map(Path, sys.argv[1:])
    request = BoundedExecutionRequest.model_validate_json(request_file.read_text(encoding="utf-8"))
    descriptor = request.descriptor_path
    workspace = AuthoringWorkspaceContext(root, descriptor)
    path = workspace.resolve_descriptor_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" keeps the bytes the parent hashed; Windows would otherwise rewrite line endings.
    path.write_text(request.xml, encoding="utf-8", newline="")
    os.chdir(root)
    staging = Path(f"{reply_file}.tmp")
    guarded, read = (
        (set(), set())
        if request.allow_side_effects
        else _contain(reply_file.parent, root, (request_file, reply_file, staging))
    )
    def read_resource(resource: Path) -> bytes:
        # The contained reader opens by dir_fd, which the open audit event does not report; record it here.
        data = workspace.read_resource_bytes(resource)
        read.add(Path(os.path.abspath(resource)).relative_to(workspace.root).as_posix())
        return data

    with resource_reader_scope(read_resource):
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
    if isinstance(message, (_WorkerSuccess, _WorkerFailure)):
        message = dataclasses.replace(message, read_files=tuple(sorted(read)))
    payload = pickle.dumps(message, protocol=pickle.HIGHEST_PROTOCOL)
    if len(payload) > _MAX_REPLY_BYTES:
        raise ValueError("bounded child evidence exceeds the transport limit")
    guarded.clear()
    staging.write_bytes(payload)
    staging.replace(reply_file)
    # Keep the tree leader alive until the parent has terminated all descendants (Windows taskkill).
    time.sleep(request.timeout_seconds + 5)


if __name__ == "__main__":
    main()
