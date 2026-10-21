# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Contain descriptor identities in the caller-owned workspace without writes."""

import os
import stat
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from datamimic_ce.authoring.adapters.windows_snapshot import WindowsSnapshotRoot
from datamimic_ce.authoring.domain.common import validate_workspace_descriptor_path

MAX_RESOURCE_BYTES = 100 * 1024 * 1024


def _same_file(before: os.stat_result, after: os.stat_result) -> bool:
    return (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )


def _read_resource_file(
    path: Path,
    before: os.stat_result,
    *,
    max_bytes: int,
    directory_fd: int | None = None,
    windows_root: WindowsSnapshotRoot | None = None,
) -> bytes:
    if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
        raise ValueError("workspace resource is not a bounded regular file")
    flags = os.O_RDONLY
    if os.name == "posix":
        flags |= os.O_NOFOLLOW | os.O_NONBLOCK
    elif sys.platform == "win32":
        flags |= os.O_BINARY
    name = path.name if directory_fd is not None else path
    descriptor = os.open(name, flags, dir_fd=directory_fd)
    with os.fdopen(descriptor, "rb") as handle:
        if windows_root is not None:
            windows_root.validate_file(handle.fileno(), path)
        opened = os.fstat(handle.fileno())
        if not stat.S_ISREG(opened.st_mode) or not _same_file(before, opened):
            raise ValueError("workspace resource changed before opening")
        data = handle.read(before.st_size + 1)
        if windows_root is not None:
            windows_root.validate_file(handle.fileno(), path)
        after = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if (
            len(data) != before.st_size
            or not _same_file(before, os.fstat(handle.fileno()))
            or not _same_file(before, after)
        ):
            raise ValueError("workspace resource changed while reading")
        return data


@dataclass(frozen=True)
class AuthoringWorkspaceContext:
    root: Path
    descriptor_path: PurePosixPath = PurePosixPath("model.xml")

    def __post_init__(self) -> None:
        validate_workspace_descriptor_path(self.descriptor_path)
        resolved_root = self.root.resolve(strict=True)
        if not resolved_root.is_dir():
            raise ValueError("authoring workspace root must be a directory")
        object.__setattr__(self, "root", resolved_root)
        self.resolve_descriptor_path()

    def resolve_descriptor_path(self, descriptor_path: PurePosixPath | None = None) -> Path:
        relative_path = validate_workspace_descriptor_path(descriptor_path or self.descriptor_path)
        resolved_path = self.root.joinpath(*relative_path.parts).resolve(strict=False)
        if not resolved_path.is_relative_to(self.root):
            raise ValueError("descriptor_path resolves outside the authoring workspace")
        return resolved_path

    def read(self, path: PurePosixPath) -> bytes:
        """One project file by its workspace path, through the same contained reader."""
        return self.read_resource_bytes(self.resolve_descriptor_path(path))

    def read_resource_bytes(self, path: Path) -> bytes:
        # Resolve lexical parents without following links before opening the rooted walk.
        absolute = Path(os.path.abspath(path))
        try:
            relative = absolute.relative_to(self.root)
        except ValueError as error:
            raise ValueError("resource lies outside the authoring workspace") from error
        if not relative.parts:
            raise ValueError("workspace root is not a resource file")
        if os.name == "posix":
            directory_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                for part in relative.parts[:-1]:
                    child_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                    os.close(directory_fd)
                    directory_fd = child_fd
                before = os.stat(relative.name, dir_fd=directory_fd, follow_symlinks=False)
                return _read_resource_file(absolute, before, max_bytes=MAX_RESOURCE_BYTES, directory_fd=directory_fd)
            finally:
                os.close(directory_fd)
        with WindowsSnapshotRoot(self.root) as windows_root:
            return _read_resource_file(
                absolute, absolute.lstat(), max_bytes=MAX_RESOURCE_BYTES, windows_root=windows_root
            )

    def load_connection_profile(self, descriptor_dir: Path, environment: str) -> dict[str, str]:
        from datamimic_ce.engine.dsl.api import parse_properties, resource_reader_active, resource_reader_scope

        if not environment or environment in {".", ".."} or "/" in environment or "\\" in environment:
            raise ValueError("environment must name one workspace-local profile")
        profile = descriptor_dir / "conf" / f"{environment}.env.properties"
        if not profile.is_relative_to(self.root):
            raise ValueError("connection profile resolves outside the authoring workspace")
        # Inside a bounded run the active reader also records the profile as a file the proof read.
        try:
            with nullcontext() if resource_reader_active() else resource_reader_scope(self.read_resource_bytes):
                return parse_properties(profile)
        except FileNotFoundError:
            return {}
