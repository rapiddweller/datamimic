# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Private Windows Job Object ownership for bounded authoring children."""

from __future__ import annotations

import ctypes
import sys
import time

_BOOL = ctypes.c_int32
_DWORD = ctypes.c_uint32
_HANDLE = ctypes.c_void_p
_INT = ctypes.c_int32
_LONG = ctypes.c_int32
_LPVOID = ctypes.c_void_p
_LPCWSTR = ctypes.c_wchar_p
_UINT = ctypes.c_uint32

_CREATE_SUSPENDED = 0x00000004
_THREAD_SUSPEND_RESUME = 0x0002
_TH32CS_SNAPTHREAD = 0x00000004
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_TERMINATE = 0x0001
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
_JOB_OBJECT_BASIC_PROCESS_ID_LIST = 3
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_MAX_TRACKED_PROCESSES = 65_536


def _windows_kernel() -> ctypes.CDLL:
    if sys.platform == "win32":
        return ctypes.WinDLL("kernel32", use_last_error=True)
    raise OSError("Windows process jobs require Windows")


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("per_process_user_time_limit", ctypes.c_longlong),
        ("per_job_user_time_limit", ctypes.c_longlong),
        ("limit_flags", _DWORD),
        ("minimum_working_set_size", ctypes.c_size_t),
        ("maximum_working_set_size", ctypes.c_size_t),
        ("active_process_limit", _DWORD),
        ("affinity", ctypes.c_size_t),
        ("priority_class", _DWORD),
        ("scheduling_class", _DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("read_operation_count", ctypes.c_ulonglong),
        ("write_operation_count", ctypes.c_ulonglong),
        ("other_operation_count", ctypes.c_ulonglong),
        ("read_transfer_count", ctypes.c_ulonglong),
        ("write_transfer_count", ctypes.c_ulonglong),
        ("other_transfer_count", ctypes.c_ulonglong),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("basic_limit_information", _BasicLimitInformation),
        ("io_info", _IoCounters),
        ("process_memory_limit", ctypes.c_size_t),
        ("job_memory_limit", ctypes.c_size_t),
        ("peak_process_memory_used", ctypes.c_size_t),
        ("peak_job_memory_used", ctypes.c_size_t),
    ]


class _BasicAccountingInformation(ctypes.Structure):
    _fields_ = [
        ("total_user_time", ctypes.c_longlong),
        ("total_kernel_time", ctypes.c_longlong),
        ("this_period_total_user_time", ctypes.c_longlong),
        ("this_period_total_kernel_time", ctypes.c_longlong),
        ("total_page_faults", _DWORD),
        ("total_processes", _DWORD),
        ("active_processes", _DWORD),
        ("total_terminated_processes", _DWORD),
    ]


class _ThreadEntry(ctypes.Structure):
    _fields_ = [
        ("size", _DWORD),
        ("usage_count", _DWORD),
        ("thread_id", _DWORD),
        ("owner_process_id", _DWORD),
        ("base_priority", _LONG),
        ("delta_priority", _LONG),
        ("flags", _DWORD),
    ]


class _ProcessIdListHeader(ctypes.Structure):
    _fields_ = [
        ("assigned_processes", _DWORD),
        ("listed_processes", _DWORD),
    ]


class WindowsProcessTree:
    """Own a process and all descendants through one kill-on-close job."""

    def __init__(self) -> None:
        kernel32 = _windows_kernel()
        kernel32.CloseHandle.argtypes = [_HANDLE]
        kernel32.CloseHandle.restype = _BOOL
        kernel32.SetInformationJobObject.argtypes = [
            _HANDLE,
            _INT,
            _LPVOID,
            _DWORD,
        ]
        kernel32.SetInformationJobObject.restype = _BOOL
        kernel32.OpenProcess.argtypes = [_DWORD, _BOOL, _DWORD]
        kernel32.OpenProcess.restype = _HANDLE
        kernel32.AssignProcessToJobObject.argtypes = [_HANDLE, _HANDLE]
        kernel32.AssignProcessToJobObject.restype = _BOOL
        kernel32.TerminateJobObject.argtypes = [_HANDLE, _UINT]
        kernel32.TerminateJobObject.restype = _BOOL
        kernel32.QueryInformationJobObject.argtypes = [
            _HANDLE,
            _INT,
            _LPVOID,
            _DWORD,
            _LPVOID,
        ]
        kernel32.QueryInformationJobObject.restype = _BOOL
        kernel32.OpenThread.argtypes = [_DWORD, _BOOL, _DWORD]
        kernel32.OpenThread.restype = _HANDLE
        kernel32.ResumeThread.argtypes = [_HANDLE]
        kernel32.ResumeThread.restype = _DWORD
        kernel32.CreateToolhelp32Snapshot.argtypes = [_DWORD, _DWORD]
        kernel32.CreateToolhelp32Snapshot.restype = _HANDLE
        kernel32.Thread32First.argtypes = [_HANDLE, ctypes.POINTER(_ThreadEntry)]
        kernel32.Thread32First.restype = _BOOL
        kernel32.Thread32Next.argtypes = [_HANDLE, ctypes.POINTER(_ThreadEntry)]
        kernel32.Thread32Next.restype = _BOOL
        kernel32.CreateJobObjectW.argtypes = [_LPVOID, _LPCWSTR]
        kernel32.CreateJobObjectW.restype = _HANDLE
        self._kernel32 = kernel32
        self._handle = kernel32.CreateJobObjectW(None, None)
        if not self._handle:
            raise OSError("bounded process job could not be created")

        information = _ExtendedLimitInformation()
        information.basic_limit_information.limit_flags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            self._handle,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(information),
            ctypes.sizeof(information),
        ):
            self.close()
            raise OSError("bounded process job could not be configured")

    def resume_suspended_process(self, process_id: int) -> bool:
        snapshot = self._kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPTHREAD, 0)
        if not snapshot or snapshot == ctypes.c_void_p(-1).value:
            return False
        thread_id: int | None = None
        entry = _ThreadEntry()
        entry.size = ctypes.sizeof(entry)
        snapshot_closed = False
        try:
            found = self._kernel32.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.owner_process_id == process_id:
                    if thread_id is not None:
                        return False
                    thread_id = entry.thread_id
                found = self._kernel32.Thread32Next(snapshot, ctypes.byref(entry))
        finally:
            snapshot_closed = bool(self._kernel32.CloseHandle(snapshot))
        if thread_id is None or not snapshot_closed:
            return False
        thread = self._kernel32.OpenThread(_THREAD_SUSPEND_RESUME, False, thread_id)
        if not thread:
            return False
        try:
            resumed = self._kernel32.ResumeThread(thread) == 1
        finally:
            thread_closed = bool(self._kernel32.CloseHandle(thread))
        return resumed and thread_closed

    def assign(self, process_id: int) -> bool:
        process_handle = self._kernel32.OpenProcess(_PROCESS_SET_QUOTA | _PROCESS_TERMINATE, False, process_id)
        if not process_handle:
            return False
        try:
            assigned = bool(self._kernel32.AssignProcessToJobObject(self._handle, process_handle))
        finally:
            process_closed = bool(self._kernel32.CloseHandle(process_handle))
        return assigned and process_closed

    def active_process_count(self) -> int | None:
        information = _BasicAccountingInformation()
        if not self._kernel32.QueryInformationJobObject(
            self._handle,
            _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
            ctypes.byref(information),
            ctypes.sizeof(information),
            None,
        ):
            return None
        return int(information.active_processes)

    def process_ids(self, deadline: float) -> tuple[int, ...] | None:
        header_size = ctypes.sizeof(_ProcessIdListHeader)
        pointer_size = ctypes.sizeof(ctypes.c_size_t)
        capacity = 64
        while time.monotonic() < deadline:
            if capacity > _MAX_TRACKED_PROCESSES:
                return None
            buffer = ctypes.create_string_buffer(header_size + capacity * pointer_size)
            returned_length = _DWORD()
            if not self._kernel32.QueryInformationJobObject(
                self._handle,
                _JOB_OBJECT_BASIC_PROCESS_ID_LIST,
                ctypes.byref(buffer),
                ctypes.sizeof(buffer),
                ctypes.byref(returned_length),
            ):
                return None
            if time.monotonic() >= deadline:
                return None
            process_list = _ProcessIdListHeader.from_buffer(buffer)
            if process_list.assigned_processes > _MAX_TRACKED_PROCESSES or process_list.listed_processes > capacity:
                return None
            if process_list.listed_processes < process_list.assigned_processes:
                capacity = max(capacity * 2, process_list.assigned_processes)
                continue
            process_ids = (ctypes.c_size_t * process_list.listed_processes).from_buffer(buffer, header_size)
            return tuple(process_ids)
        return None

    def terminate(self) -> bool:
        return bool(self._kernel32.TerminateJobObject(self._handle, 1))

    def close(self) -> bool:
        handle = self._handle
        if handle:
            self._handle = None
            return bool(self._kernel32.CloseHandle(handle))
        return True
