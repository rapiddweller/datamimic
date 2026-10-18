# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Verify opened Windows files against one retained workspace directory identity."""

from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes
from pathlib import Path
from types import TracebackType


def _windows_error() -> OSError:
    if sys.platform == "win32":
        return ctypes.WinError(ctypes.get_last_error())
    return OSError("Windows snapshot handles require Windows")


def _windows_kernel() -> ctypes.CDLL:
    if sys.platform == "win32":
        return ctypes.WinDLL("kernel32", use_last_error=True)
    raise OSError("Windows snapshot handles require Windows")


class _FileInformation(ctypes.Structure):
    _fields_ = [
        ("attributes", wintypes.DWORD),
        ("creation", wintypes.FILETIME),
        ("access", wintypes.FILETIME),
        ("write", wintypes.FILETIME),
        ("volume", wintypes.DWORD),
        ("size_high", wintypes.DWORD),
        ("size_low", wintypes.DWORD),
        ("links", wintypes.DWORD),
        ("index_high", wintypes.DWORD),
        ("index_low", wintypes.DWORD),
    ]


class WindowsSnapshotRoot:
    def __init__(self, root: Path) -> None:
        kernel = _windows_kernel()
        self._root = root.absolute()
        self._open = kernel.CreateFileW
        self._open.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        self._open.restype = wintypes.HANDLE
        self._close = kernel.CloseHandle
        self._close.argtypes = [wintypes.HANDLE]
        self._close.restype = wintypes.BOOL
        self._path = kernel.GetFinalPathNameByHandleW
        self._path.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
        self._path.restype = wintypes.DWORD
        self._info = kernel.GetFileInformationByHandle
        self._info.argtypes = [wintypes.HANDLE, ctypes.POINTER(_FileInformation)]
        self._info.restype = wintypes.BOOL
        self._handle = self._open_directory(self._root)
        try:
            self._root_path = self._final_path(self._handle)
            self._root_identity = self._identity(self._handle)
            if self._root_path != self._normalized(self._root):
                raise ValueError("workspace root resolves through a reparse point")
        except BaseException:
            self._close(self._handle)
            raise

    def __enter__(self) -> WindowsSnapshotRoot:
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, traceback: TracebackType | None
    ) -> None:
        if not self._close(self._handle):
            raise _windows_error()

    @staticmethod
    def _normalized(path: Path) -> Path:
        return Path(os.path.normcase(os.path.normpath(str(path))))

    def _information(self, handle: int) -> _FileInformation:
        information = _FileInformation()
        if not self._info(handle, ctypes.byref(information)):
            raise _windows_error()
        if information.attributes & 0x400:  # FILE_ATTRIBUTE_REPARSE_POINT
            raise ValueError("workspace contains a reparse point")
        return information

    def _identity(self, handle: int) -> tuple[int, int, int]:
        information = self._information(handle)
        return information.volume, information.index_high, information.index_low

    def _open_directory(self, path: Path) -> int:
        # Retain a directory handle while permitting identity checks during concurrent renames.
        handle = self._open(str(path), 0x80, 0x7, None, 3, 0x02200000, None)
        if handle is None or handle == ctypes.c_void_p(-1).value:
            raise _windows_error()
        return handle

    def _final_path(self, handle: int) -> Path:
        length = self._path(handle, None, 0, 0)
        if not length or length > 32768:
            raise OSError("opened workspace path cannot be represented safely")
        buffer = ctypes.create_unicode_buffer(length + 1)
        written = self._path(handle, buffer, len(buffer), 0)
        if not written or written >= len(buffer):
            raise _windows_error()
        value = buffer.value
        if value.startswith("\\\\?\\UNC\\"):
            value = "\\\\" + value[8:]
        elif value.startswith("\\\\?\\"):
            value = value[4:]
        return self._normalized(Path(value))

    def _validate_root(self) -> None:
        current = self._open_directory(self._root)
        try:
            if (
                self._identity(current) != self._root_identity
                or self._final_path(current) != self._root_path
                or self._final_path(self._handle) != self._root_path
            ):
                raise ValueError("workspace root identity changed")
        finally:
            self._close(current)

    def _validate_handle(self, handle: int, expected_path: Path) -> None:
        self._validate_root()
        self._information(handle)
        actual = self._final_path(handle)
        if actual != self._normalized(expected_path.absolute()) or not actual.is_relative_to(self._root_path):
            raise ValueError("opened workspace resource is outside its expected root identity")

    def validate_directory(self, path: Path) -> None:
        handle = self._open_directory(path)
        try:
            self._validate_handle(handle, path)
        finally:
            self._close(handle)

    def validate_file(self, descriptor: int, expected_path: Path) -> None:
        if sys.platform == "win32":
            import msvcrt

            self._validate_handle(msvcrt.get_osfhandle(descriptor), expected_path)
        else:
            raise OSError("Windows snapshot handles require Windows")
