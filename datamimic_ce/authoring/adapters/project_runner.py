# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Run the project entry in a child process and report what it wrote."""

from __future__ import annotations

import getpass
import hashlib
import io
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from collections import deque
from collections.abc import Mapping
from importlib import metadata
from pathlib import Path, PurePath, PurePosixPath
from typing import Literal

from datamimic_ce.authoring.adapters.bounded_executor import _terminate_process_tree
from datamimic_ce.authoring.adapters.workspace import AuthoringWorkspaceContext
from datamimic_ce.authoring.domain.project_run import (
    LOG_TAIL_LINES,
    MAX_LISTED_ARTIFACTS,
    ProjectArtifact,
    ProjectParam,
    ProjectRunExecution,
    ProjectRunRecord,
)
from datamimic_ce.authoring.domain.requests import PROJECT_ENTRY_PATH, BuildArtifact

RECORD_FOLDER = "docs/runs"
_UTC_SECONDS = "%Y-%m-%dT%H:%M:%SZ"
_UTC_STAMP = "%Y%m%dT%H%M%SZ"

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


def _sha256(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256")
    except OSError:
        return None
    return digest.hexdigest()


def _actor() -> str | None:
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return None


def _log_tail(descriptor: int) -> tuple[str, ...]:
    size = os.fstat(descriptor).st_size
    os.lseek(descriptor, max(0, size - _LOG_READ_BYTES), os.SEEK_SET)
    data = os.read(descriptor, _LOG_READ_BYTES)
    last = deque(io.StringIO(str(data, "utf-8", "replace"), newline=None), maxlen=LOG_TAIL_LINES)
    return tuple(line[:-1] if line[-1:] == "\n" else line for line in last)


class CeProjectRunner:
    def __init__(self, workspace: AuthoringWorkspaceContext, environment: Mapping[str, str] | None = None) -> None:
        self._workspace = workspace
        self._root = workspace.root
        self._environment = {**os.environ, **(environment or {})}

    def _mismatched_build_files(self, artifact: BuildArtifact) -> set[str]:
        mismatches: set[str] = set()
        for item in artifact.files:
            try:
                data = self._workspace.read_project_file(item.path)
                digest = hashlib.sha256(data).hexdigest()
            except (OSError, ValueError, RuntimeError):
                # Path.resolve() may raise RuntimeError for a symlink loop on Python 3.11.
                digest = None
            if digest != item.sha256:
                mismatches.add(str(item.path))
        return mismatches

    def run(
        self,
        params: tuple[ProjectParam, ...],
        timeout_seconds: int,
        proof: BuildArtifact | None = None,
        *,
        build_outcome: Literal["ready", "ready_with_gaps"] | None = None,
    ) -> ProjectRunExecution:
        # The task id names output/<task id>, so the record and the output files link to each other.
        task_id = uuid.uuid4().hex
        # -P keeps the project directory off sys.path: a project file named like a module must not replace it.
        command = [sys.executable, "-P", "-m", "datamimic_ce.interfaces.cli", "run", PROJECT_ENTRY_PATH.as_posix()]
        command += ["--task-id", task_id]
        for param in params:
            command += ["--param", f"{param.name}={param.value}"]
        before = _snapshot(self._root)
        started_at = time.gmtime()
        started = time.monotonic()
        descriptor, log_path = tempfile.mkstemp(prefix="datamimic-run-")
        try:
            try:
                mismatches = self._mismatched_build_files(proof) if proof is not None else None
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
                        _terminate_process_tree(process)
                        timed_out = True
                if timed_out:
                    exit_code = None
                if mismatches is not None and proof is not None:
                    mismatches.update(self._mismatched_build_files(proof))
                tail = _log_tail(descriptor)
            finally:
                os.close(descriptor)
            duration = time.monotonic() - started
            after = _snapshot(self._root)
            changed = sorted(path for path in after if before.get(path) != after[path])
            artifacts = tuple(
                ProjectArtifact(path=path, bytes=after[path][0], sha256=_sha256(self._root / path))
                for path in changed[:MAX_LISTED_ARTIFACTS]
            )
            outcome: Literal["completed", "failed", "timeout"] = (
                "timeout" if timed_out else "completed" if exit_code == 0 else "failed"
            )
            ended_at = time.gmtime()
            build_file_mismatches = tuple(sorted(mismatches)) if mismatches is not None else None
            record = ProjectRunRecord(
                task_id=task_id,
                actor=_actor(),
                started_utc=time.strftime(_UTC_SECONDS, started_at),
                ended_utc=time.strftime(_UTC_SECONDS, ended_at),
                ce_version=metadata.version("datamimic_ce"),
                python_version=platform.python_version(),
                param_names=tuple(param.name for param in params),
                proof=proof,
                build_outcome=build_outcome,
                build_file_mismatches=build_file_mismatches,
                outcome=outcome,
                exit_code=exit_code,
                duration_seconds=round(duration, 3),
                outputs=artifacts,
                output_count=len(changed),
                log="run.log",
            )
            record_path = self._write_record(record, started_at, Path(log_path))
        finally:
            os.unlink(log_path)
        return ProjectRunExecution(
            exit_code=exit_code,
            timed_out=timed_out,
            duration_seconds=round(duration, 3),
            artifacts=artifacts,
            artifact_count=len(changed),
            log_tail=tail,
            record_path=record_path,
            build_file_mismatches=build_file_mismatches,
        )

    def _write_record(self, record: ProjectRunRecord, started_at: time.struct_time, log: Path) -> str | None:
        """Keep the full log and the record beside the project. A run that already ended must not fail here."""
        folder = f"{RECORD_FOLDER}/{time.strftime(_UTC_STAMP, started_at)}_{record.task_id}"
        directory = self._root / folder
        root = os.path.realpath(self._root)
        # docs/ may be a link out of the project: the record must stay inside it.
        if os.path.commonpath([root, os.path.realpath(directory)]) != root:
            return None
        text = record.model_dump_json(indent=2) + "\n"
        try:
            os.makedirs(directory)
            # An error message of the engine can quote a parameter value, so the full log stays private to the user.
            descriptor = os.open(directory / record.log, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as target, open(log, "rb") as source:
                shutil.copyfileobj(source, target)
            (directory / "run.json").write_text(text, encoding="utf-8")
        except OSError:
            return None
        return folder
