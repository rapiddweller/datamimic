# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Run the project entry in a child process and report what it wrote."""

from __future__ import annotations

import io
import os
import signal
import subprocess
import sys
import tempfile
import time
from collections import deque
from collections.abc import Mapping
from pathlib import Path, PurePath, PurePosixPath

from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.project_run import (
    LOG_TAIL_LINES,
    MAX_LISTED_ARTIFACTS,
    ProjectArtifact,
    ProjectParam,
    ProjectRunExecution,
)
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH

_FileStamp = tuple[int, int]
_LOG_READ_BYTES = 1024 * 1024


def _snapshot(root: Path) -> dict[str, _FileStamp]:
    stamps: dict[str, _FileStamp] = {}
    for directory, names, files in os.walk(root):
        names[:] = [name for name in names if name[:1] != "." and name != "__pycache__"]
        for name in files:
            path = os.path.join(directory, name)
            if os.path.islink(path):
                continue
            try:
                status = os.stat(path)
            except OSError:
                continue
            relative = str(PurePosixPath(*PurePath(os.path.relpath(path, root)).parts))
            stamps[relative] = (status.st_size, status.st_mtime_ns)
    return stamps


def _log_tail(descriptor: int) -> tuple[str, ...]:
    size = os.fstat(descriptor).st_size
    os.lseek(descriptor, max(0, size - _LOG_READ_BYTES), os.SEEK_SET)
    data = os.read(descriptor, _LOG_READ_BYTES)
    last = deque(io.StringIO(str(data, "utf-8", "replace"), newline=None), maxlen=LOG_TAIL_LINES)
    return tuple(line[:-1] if line[-1:] == "\n" else line for line in last)


def _stop(process: subprocess.Popen[bytes]) -> None:
    if os.name == "posix":
        os.killpg(process.pid, signal.SIGKILL)
    else:
        os.kill(process.pid, signal.SIGTERM)


class CeProjectRunner:
    def __init__(self, workspace: AuthoringWorkspaceContext, environment: Mapping[str, str] | None = None) -> None:
        self._root = workspace.root
        self._environment = {**os.environ, **(environment or {})}

    def run(self, params: tuple[ProjectParam, ...], timeout_seconds: int) -> ProjectRunExecution:
        # -P keeps the project directory off sys.path: a project file named like a module must not replace it.
        command = [sys.executable, "-P", "-m", "datamimic_ce.interfaces.cli", "run", PROJECT_ENTRY_PATH.as_posix()]
        for param in params:
            command += ["--param", f"{param.name}={param.value}"]
        before = _snapshot(self._root)
        started = time.monotonic()
        descriptor, log_path = tempfile.mkstemp(prefix="datamimic-run-")
        try:
            process = subprocess.Popen(  # noqa: S603 - fixed interpreter and arguments, no shell
                command,
                cwd=self._root,
                env=self._environment,
                stdin=subprocess.DEVNULL,
                stdout=descriptor,
                stderr=subprocess.STDOUT,
                start_new_session=os.name == "posix",
            )
            exit_code: int | None = None
            timed_out = False
            # The second pass reaps the child that the stop ended.
            for limit in (timeout_seconds, None):
                try:
                    exit_code = process.wait(timeout=limit)
                    break
                except subprocess.TimeoutExpired:
                    _stop(process)
                    timed_out = True
            if timed_out:
                exit_code = None
            tail = _log_tail(descriptor)
        finally:
            os.close(descriptor)
            os.unlink(log_path)
        duration = time.monotonic() - started
        after = _snapshot(self._root)
        changed = sorted(path for path in after if before.get(path) != after[path])
        return ProjectRunExecution(
            exit_code=exit_code,
            timed_out=timed_out,
            duration_seconds=round(duration, 3),
            artifacts=tuple(
                ProjectArtifact(path=path, bytes=after[path][0]) for path in changed[:MAX_LISTED_ARTIFACTS]
            ),
            artifact_count=len(changed),
            log_tail=tail,
        )
