# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Private workspace and process ownership for one bounded CE execution."""

from __future__ import annotations

import base64
import json
import os
import pickle
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import suppress
from dataclasses import dataclass, field, replace
from itertools import islice
from pathlib import Path
from uuid import uuid4

import psutil
from lxml import etree
from pydantic import SecretBytes

from datamimic_ce.authoring.adapters import dryrun
from datamimic_ce.authoring.adapters.windows_process_tree import _CREATE_SUSPENDED, WindowsProcessTree
from datamimic_ce.authoring.adapters.windows_snapshot import WindowsSnapshotRoot
from datamimic_ce.authoring.adapters.workspace import (
    MAX_RESOURCE_BYTES,
    AuthoringWorkspaceContext,
    _read_resource_file,
    _same_file,
)
from datamimic_ce.authoring.domain.capture import CapturedProducts
from datamimic_ce.authoring.domain.diagnostics import (
    AuthoringRuleId,
    AuthoringSystemDiagnosticCode,
    CeErrorIdentity,
    Diagnostic,
    DiagnosticPhase,
)
from datamimic_ce.authoring.domain.requests import (
    BoundedExecutionEvidence,
    BoundedExecutionRequest,
    SourceAccessEvidence,
)
from datamimic_ce.engine.runtime.contracts import PseudonymizationKey
from datamimic_ce.errors import DomainError, GeneratorConfigError, UserErrorBase
from datamimic_ce.errors.catalog import get_issue_definition
from datamimic_ce.errors.codes import ErrorCode

_MAX_WORKSPACE_BYTES = 256 * 1024 * 1024
_MAX_WORKSPACE_FILE_BYTES = MAX_RESOURCE_BYTES
_MAX_WORKSPACE_FILES = 2_000
_MAX_WORKSPACE_ENTRIES = 4_000
_MAX_WORKSPACE_DEPTH = 64
_MAX_REPLY_BYTES = dryrun._MAX_WORKER_REPLY_BYTES
_PROCESS_TREE_CLEANUP_SECONDS = 1.25


@dataclass(frozen=True, slots=True, repr=False)
class _LiveBoundedKeyEnvelope:
    call_id: str
    key: bytes | None = field(repr=False)

    def serialize(self) -> str:
        return json.dumps(
            {
                "call_id": self.call_id,
                "pseudonymization_key": base64.b64encode(self.key).decode("ascii") if self.key is not None else None,
            },
            separators=(",", ":"),
        )


def _failure(code: AuthoringSystemDiagnosticCode, message: str, max_count: int) -> BoundedExecutionEvidence:
    diagnostic = Diagnostic(
        code=code,
        phase=DiagnosticPhase.EVIDENCE,
        message=message,
        remediation="Repair the bounded descriptor or its workspace resources, then retry.",
    )
    return BoundedExecutionEvidence(
        ok=False, captured=CapturedProducts((), max_count), diagnostics=(diagnostic,), base_run_ok=False
    )


def _snapshot_workspace(source: Path, destination: Path) -> None:
    """Read bounded regular files without following links; verify opened identities."""
    file_count = 0
    entry_count = 0
    total_bytes = 0
    windows_root: WindowsSnapshotRoot | None = None
    destination.mkdir()

    def copy_file(source_path: Path, output_path: Path, before: os.stat_result, *, directory_fd: int | None) -> None:
        nonlocal file_count, total_bytes
        file_count += 1
        total_bytes += before.st_size
        if (
            file_count > _MAX_WORKSPACE_FILES
            or before.st_size > _MAX_WORKSPACE_FILE_BYTES
            or total_bytes > _MAX_WORKSPACE_BYTES
        ):
            raise ValueError("workspace exceeds bounded snapshot limits")
        data = _read_resource_file(
            source_path,
            before,
            max_bytes=_MAX_WORKSPACE_FILE_BYTES,
            directory_fd=directory_fd,
            windows_root=windows_root,
        )
        with output_path.open("xb") as output_file:
            output_file.write(data)

    def copy_directory(source_path: Path, output_path: Path, directory_fd: int | None = None, depth: int = 0) -> None:
        nonlocal entry_count
        if depth > _MAX_WORKSPACE_DEPTH:
            raise ValueError("workspace exceeds bounded directory depth")
        if windows_root is not None:
            windows_root.validate_directory(source_path)
        before = os.fstat(directory_fd) if directory_fd is not None else source_path.lstat()
        if not stat.S_ISDIR(before.st_mode):
            raise ValueError("workspace contains a symbolic link or non-directory root")
        with os.scandir(directory_fd if directory_fd is not None else source_path) as entries:
            remaining = _MAX_WORKSPACE_ENTRIES - entry_count
            bounded_entries = list(islice(entries, remaining + 1))
            if len(bounded_entries) > remaining:
                raise ValueError("workspace exceeds bounded entry count")
            for entry in sorted(bounded_entries, key=lambda item: item.name):
                entry_count += 1
                if entry_count > _MAX_WORKSPACE_ENTRIES:
                    raise ValueError("workspace exceeds bounded entry count")
                path = source_path / entry.name
                # Windows DirEntry.stat omits the file identity required by the opened-handle check.
                info = os.stat(
                    entry.name if directory_fd is not None else path,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                output = output_path / entry.name
                if stat.S_ISREG(info.st_mode):
                    copy_file(path, output, info, directory_fd=directory_fd)
                elif stat.S_ISDIR(info.st_mode):
                    # Host Python environments are not model resources.
                    if depth == 0 and entry.name in {".venv", "venv"}:
                        continue
                    output.mkdir()
                    if os.name == "posix":
                        child_fd = os.open(
                            entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd
                        )
                        try:
                            if not _same_file(info, os.fstat(child_fd)):
                                raise ValueError("workspace directory was replaced")
                            copy_directory(path, output, child_fd, depth + 1)
                        finally:
                            os.close(child_fd)
                    else:
                        copy_directory(path, output, depth=depth + 1)
                else:
                    raise ValueError("workspace contains a symbolic link or special file")
        after = os.fstat(directory_fd) if directory_fd is not None else source_path.lstat()
        if not _same_file(before, after):
            raise ValueError("workspace directory changed during copying")

    if os.name == "posix":
        root_fd = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            copy_directory(source, destination, root_fd)
        finally:
            os.close(root_fd)
    else:
        with WindowsSnapshotRoot(source) as windows_root:
            copy_directory(source, destination)


def _terminate_process_tree(
    process: subprocess.Popen[bytes],
    writer_thread: threading.Thread | None = None,
    windows_job: WindowsProcessTree | None = None,
) -> bool:
    """Stop the worker and confirm its owned process tree is gone."""
    deadline = time.monotonic() + _PROCESS_TREE_CLEANUP_SECONDS
    cleanup_ok = True
    if windows_job is not None:
        tree_stopped = _windows_tree_is_stopped(process, windows_job, deadline)
        if tree_stopped is None:
            cleanup_ok = False
            if time.monotonic() < deadline:
                cleanup_ok = windows_job.terminate() and cleanup_ok
        elif not tree_stopped:
            cleanup_ok = windows_job.terminate()
    elif os.name == "posix":
        cleanup_ok = _kill_process_group(process.pid, signal.SIGTERM)
    else:
        try:
            process.terminate()
        except ProcessLookupError:
            pass
        except OSError:
            cleanup_ok = False

    with suppress(subprocess.TimeoutExpired):
        process.wait(timeout=min(0.25, max(0, deadline - time.monotonic())))

    if windows_job is None:
        if os.name == "posix":
            cleanup_ok = _kill_process_group(process.pid, signal.SIGKILL) and cleanup_ok
        elif process.poll() is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            except OSError:
                cleanup_ok = False

    while True:
        process_stopped = process.poll() is not None
        if windows_job is not None:
            tree_stopped = _windows_tree_is_stopped(process, windows_job, deadline)
            if tree_stopped is None:
                cleanup_ok = False
                if time.monotonic() < deadline:
                    cleanup_ok = windows_job.terminate() and cleanup_ok
            elif tree_stopped:
                break
        elif process_stopped and (os.name != "posix" or _process_group_is_absent(process.pid)):
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            cleanup_ok = False
            break
        if process_stopped:
            time.sleep(min(0.05, remaining))
        else:
            with suppress(subprocess.TimeoutExpired):
                process.wait(timeout=min(0.05, remaining))

    if writer_thread is not None:
        writer_thread.join(timeout=max(0, deadline - time.monotonic()))
    writer_stopped = writer_thread is None or not writer_thread.is_alive()
    if windows_job is not None:
        cleanup_ok = windows_job.close() and cleanup_ok
    else:
        tree_stopped = process.poll() is not None and (os.name != "posix" or _process_group_is_absent(process.pid))
    return tree_stopped is True and writer_stopped and cleanup_ok


def _windows_tree_is_stopped(
    process: subprocess.Popen[bytes], windows_job: WindowsProcessTree, deadline: float
) -> bool | None:
    if windows_job.active_process_count() is None:
        return None
    process_ids = windows_job.process_ids(deadline)
    if process_ids is None or process.poll() is None:
        return None if process_ids is None else False
    return not any(process_id != process.pid for process_id in process_ids)


def _kill_process_group(group_id: int, sig: signal.Signals) -> bool:
    try:
        os.killpg(group_id, sig)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    return True


def _process_group_is_absent(group_id: int) -> bool:
    try:
        os.killpg(group_id, 0)
    except ProcessLookupError:
        return True
    except OSError:
        return False
    for process in psutil.process_iter():
        try:
            process_group_id = os.getpgid(process.pid)
        except psutil.NoSuchProcess:
            continue
        except OSError:
            return False
        if process_group_id != group_id:
            continue
        try:
            if process.status() != psutil.STATUS_ZOMBIE:
                return False
        except psutil.NoSuchProcess:
            continue
        except (psutil.AccessDenied, OSError):
            return False
    return True


def _append_cleanup_failure(result: BoundedExecutionEvidence, max_count: int) -> BoundedExecutionEvidence:
    cleanup_failure = _failure(
        AuthoringSystemDiagnosticCode.CLEANUP,
        "Bounded process tree could not be terminated and reaped.",
        max_count,
    )
    if result.ok:
        return cleanup_failure
    return replace(
        result,
        ok=False,
        diagnostics=result.diagnostics + cleanup_failure.diagnostics,
        base_run_ok=False,
    )


def _is_windows_platform() -> bool:
    return os.name == "nt"


def _decode_reply(payload: bytes, request: BoundedExecutionRequest) -> BoundedExecutionEvidence:
    try:
        message = dryrun._decode_worker_message(payload, max_count=request.max_count)
        if isinstance(message, dryrun._WorkerFailure):
            identity = None
            if isinstance(message.error, (UserErrorBase, DomainError)) and isinstance(message.error.code, ErrorCode):
                identity = CeErrorIdentity(
                    error_code=message.error.code,
                    issue_code=message.error.issue_code if isinstance(message.error, UserErrorBase) else None,
                )
            location = message.error.location if isinstance(message.error, UserErrorBase) else None
            definition = (
                get_issue_definition(message.error.issue_code)
                if isinstance(message.error, UserErrorBase) and message.error.issue_code is not None
                else None
            )
            entry = request.descriptor_path.as_posix()
            path: tuple[str, ...] = ("descriptor", entry)
            if location is not None:
                # A failure inside an included step names that step (its literal workspace uri), not the entry.
                if location.descriptor_path is not None and location.descriptor_path != entry:
                    path = ("include", location.descriptor_path)
                path += (location.element_tag,)
                if location.attribute is not None:
                    path += (location.attribute,)
            constructor_reason = (
                message.error.constructor_reason if isinstance(message.error, GeneratorConfigError) else None
            )
            diagnostic = Diagnostic(
                code=AuthoringRuleId.SIDE_EFFECT
                if message.policy_refusal
                else AuthoringSystemDiagnosticCode.CHILD_EXECUTION,
                phase=DiagnosticPhase.POLICY if message.policy_refusal else DiagnosticPhase.EVIDENCE,
                message=(
                    constructor_reason
                    if constructor_reason is not None
                    else f"{definition.title} at {'/'.join(path)}."
                    if definition is not None
                    else message.message
                    if message.policy_refusal
                    else "Bounded CE execution failed."
                ),
                remediation=(
                    "Correct the generator parameters using the supported values and bounds in this diagnostic."
                    if constructor_reason is not None
                    else dryrun._runtime_hint(message.error)
                    if isinstance(message.error, UserErrorBase | DomainError)
                    # The worker's hint for an untyped error is static text chosen by its type.
                    else message.fix_hint
                ),
                ce_error=identity,
                path=path,
            )
            return BoundedExecutionEvidence(
                ok=False, captured=CapturedProducts((), request.max_count), diagnostics=(diagnostic,), base_run_ok=False
            )
        if not isinstance(message, dryrun._WorkerSuccess):
            raise ValueError("unknown worker response")
        captured = dryrun._captured_products(message, request.max_count)
        diagnostics = tuple(
            Diagnostic(
                code=AuthoringSystemDiagnosticCode.CHILD_EXECUTION,
                phase=DiagnosticPhase.EVIDENCE,
                message="A captured row failed the requested file-export smoke check.",
                remediation="Repair the file exporter configuration or generated value types.",
                path=("descriptor", request.descriptor_path.as_posix()),
            )
            for _ in message.smoke_diagnostics
        )
        base_run_ok = any(product.rows for product in captured.products)
        if not base_run_ok:
            diagnostics += (
                Diagnostic(
                    code=AuthoringSystemDiagnosticCode.NOT_EXECUTED,
                    phase=DiagnosticPhase.EVIDENCE,
                    message="Bounded execution produced no captured rows.",
                    remediation="Use a descriptor that produces the required bounded data.",
                ),
            )
        return BoundedExecutionEvidence(
            ok=base_run_ok and not diagnostics,
            captured=captured,
            diagnostics=diagnostics,
            smoke_export=message.smoke_export,
            source_accesses=tuple(
                SourceAccessEvidence(source_type=source_type, requests=count)
                for source_type, count in message.source_accesses
            ),
            base_run_ok=base_run_ok,
        )
    except (
        AttributeError,
        ImportError,
        EOFError,
        LookupError,
        OverflowError,
        RecursionError,
        pickle.PickleError,
        TypeError,
        ValueError,
    ):
        return _failure(
            AuthoringSystemDiagnosticCode.SERIALIZATION,
            "Bounded child returned invalid capture evidence.",
            request.max_count,
        )


def _requires_workspace_snapshot(request: BoundedExecutionRequest, workspace: AuthoringWorkspaceContext) -> bool:
    """Only omit host files when registered DSL facts prove no resource dependency.

    Arbitrary expressions and extensions stay on the bounded full-snapshot path;
    their file dependencies cannot be inferred from XML declarations.
    """
    from datamimic_ce.domains.api import iter_generator_types
    from datamimic_ce.engine.dsl.api import DescriptorParser, get_element_definition, parse_xml_source
    from datamimic_ce.engine.dsl.vocabulary.contracts.dsl_element import BoundedExecutionStrategy

    root = parse_xml_source(request.xml)
    generators = {generator.__name__ for generator in iter_generator_types()}
    requires_snapshot = False
    descriptor_dir = workspace.resolve_descriptor_path().parent

    def check_resource(value: str) -> None:
        relative = Path(value)
        if relative.is_absolute() or "\\" in value:
            raise ValueError("workspace resources must use relative contained paths")
        if not (descriptor_dir / relative).resolve(strict=False).is_relative_to(workspace.root):
            raise ValueError("workspace resource resolves outside the bound root")

    from datamimic_ce.engine.dsl.vocabulary.source_capabilities import source_file_format_for

    for element in root.iter():
        if not isinstance(element.tag, str):
            continue
        definition = get_element_definition(element.tag)
        if definition is None:
            requires_snapshot = True
            continue
        if definition.client_family:
            requires_snapshot = True
        source = element.attrib.get("source")
        if source is not None and source_file_format_for(element.tag, source, element.attrib.get("type")) is not None:
            check_resource(source)
        export_uri = element.attrib.get("exportUri")
        if export_uri is not None:
            check_resource(export_uri)
        uri = element.attrib.get("uri")
        if uri is not None:
            check_resource(uri)
        if definition.tag == "demographics":
            check_resource(element.attrib.get("directory", "."))
        profile = definition.bounded_execution_profile
        # A library may read workspace files, and inline code names none in its attributes.
        if (
            profile.strategy in (BoundedExecutionStrategy.UNSUPPORTED, BoundedExecutionStrategy.PYTHON_LIBRARY)
            or profile.dependency_attribute
        ):
            requires_snapshot = True
        # These are exact DSL attribute names, not searches in source text.
        if set(element.attrib) & {"source", "uri", "script", "condition", "selector", "converter"}:
            requires_snapshot = True
        generator = element.attrib.get("generator")
        if generator is not None and generator not in generators:
            requires_snapshot = True
        if definition.tag in {"demographics", "generator", "assert", "if", "else-if", "while"}:
            requires_snapshot = True
    if requires_snapshot:
        return True
    # Apply the actual parser as the final proof, with the same contained loader.
    DescriptorParser.parse_xml(
        request.xml,
        workspace.resolve_descriptor_path(),
        dict(request.environment_properties),
        "production",
        profile_loader=workspace.load_connection_profile,
        logical_descriptor_path=request.descriptor_path.as_posix(),
    )
    return False


class CeBoundedExecutor:
    def __init__(self, workspace_context: AuthoringWorkspaceContext | None = None) -> None:
        self._workspace_context = workspace_context

    def execute(
        self, request: BoundedExecutionRequest, *, pseudonymization_key: SecretBytes | None = None
    ) -> BoundedExecutionEvidence:
        from datamimic_ce.domains.api import configured_dataset_overrides

        request = BoundedExecutionRequest.model_validate_json(request.model_dump_json())
        if configured_dataset_overrides():
            return _failure(
                AuthoringSystemDiagnosticCode.ENVIRONMENT,
                "Bounded execution does not support configured external Domain dataset roots.",
                request.max_count,
            )
        workspace = self._workspace_context
        if workspace is not None and request.descriptor_path != workspace.descriptor_path:
            return _failure(
                AuthoringSystemDiagnosticCode.DESCRIPTOR,
                "Descriptor path does not match the bound workspace.",
                request.max_count,
            )
        result: BoundedExecutionEvidence
        temporary = tempfile.TemporaryDirectory(prefix="datamimic-bounded-")
        try:
            private_root = Path(temporary.name)
            private_workspace = private_root / "workspace"
            try:
                if workspace is None:
                    private_workspace.mkdir()
                    _requires_workspace_snapshot(
                        request, AuthoringWorkspaceContext(private_workspace, request.descriptor_path)
                    )
                else:
                    if _requires_workspace_snapshot(request, workspace):
                        _snapshot_workspace(workspace.root, private_workspace)
                    else:
                        private_workspace.mkdir()
                request_file = private_root / "request.json"
                request_file.write_text(request.model_dump_json(), encoding="utf-8")
            except (OSError, ValueError, etree.XMLSyntaxError):
                result = _failure(
                    AuthoringSystemDiagnosticCode.ENVIRONMENT,
                    "Bounded workspace could not be copied safely.",
                    request.max_count,
                )
            else:
                execution_key = (
                    PseudonymizationKey(pseudonymization_key.get_secret_value())
                    if pseudonymization_key is not None
                    else None
                )
                result = self._execute_child(
                    request, private_workspace, request_file, private_root / "reply.pickle", execution_key
                )
        finally:
            try:
                temporary.cleanup()
            except OSError:
                result = _failure(
                    AuthoringSystemDiagnosticCode.CLEANUP,
                    "Private bounded workspace could not be removed.",
                    request.max_count,
                )
        return result

    @staticmethod
    def _execute_child(
        request: BoundedExecutionRequest,
        workspace: Path,
        request_file: Path,
        reply_file: Path,
        pseudonymization_key: PseudonymizationKey | None,
    ) -> BoundedExecutionEvidence:
        call_id = uuid4().hex
        command = [
            sys.executable,
            "-P",
            "-m",
            "datamimic_ce.authoring.adapters.bounded_executor_child",
            str(request_file),
            str(reply_file),
            str(workspace),
            call_id,
        ]
        windows_job: WindowsProcessTree | None = None
        result: BoundedExecutionEvidence | None = None
        if _is_windows_platform():
            try:
                windows_job = WindowsProcessTree()
            except OSError:
                return _failure(
                    AuthoringSystemDiagnosticCode.CHILD_CRASH,
                    "Bounded child process ownership could not be created.",
                    request.max_count,
                )
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=os.name == "posix",
                creationflags=_CREATE_SUSPENDED if windows_job is not None else 0,
            )
        except OSError:
            result = _failure(
                AuthoringSystemDiagnosticCode.CHILD_CRASH, "Bounded child could not start.", request.max_count
            )
            if windows_job is not None and not windows_job.close():
                return _append_cleanup_failure(result, request.max_count)
            return result
        if windows_job is not None:
            if not windows_job.assign(process.pid):
                result = _failure(
                    AuthoringSystemDiagnosticCode.CHILD_CRASH,
                    "Bounded child could not enter its process job.",
                    request.max_count,
                )
                try:
                    process.kill()
                    process.wait(timeout=_PROCESS_TREE_CLEANUP_SECONDS)
                    stopped = process.poll() is not None
                except (OSError, subprocess.TimeoutExpired):
                    stopped = False
                if not windows_job.close() or not stopped:
                    return _append_cleanup_failure(result, request.max_count)
                return result
            if not windows_job.resume_suspended_process(process.pid):
                result = _failure(
                    AuthoringSystemDiagnosticCode.CHILD_CRASH,
                    "Bounded child could not resume in its process job.",
                    request.max_count,
                )
                if not _terminate_process_tree(process, windows_job=windows_job):
                    return _append_cleanup_failure(result, request.max_count)
                return result
        deadline = time.monotonic() + request.timeout_seconds
        input_ready = threading.Event()
        input_errors: list[OSError] = []
        live_input = (
            _LiveBoundedKeyEnvelope(call_id, pseudonymization_key.value if pseudonymization_key is not None else None)
            .serialize()
            .encode("utf-8")
        )

        def deliver_input() -> None:
            try:
                if process.stdin is None:
                    raise BrokenPipeError("bounded child input pipe is unavailable")
                process.stdin.write(live_input)
                process.stdin.close()
            except OSError as error:
                input_errors.append(error)
            finally:
                input_ready.set()

        input_thread = threading.Thread(target=deliver_input, daemon=True)
        input_thread.start()
        try:
            while not reply_file.exists():
                if process.poll() is not None:
                    result = _failure(
                        AuthoringSystemDiagnosticCode.CHILD_CRASH,
                        f"Bounded child exited without evidence (exit code {process.returncode}).",
                        request.max_count,
                    )
                    break
                if input_ready.is_set() and input_errors:
                    result = _failure(
                        AuthoringSystemDiagnosticCode.CHILD_CRASH,
                        "Bounded child could not receive its private input.",
                        request.max_count,
                    )
                    break
                if time.monotonic() >= deadline:
                    result = _failure(
                        AuthoringSystemDiagnosticCode.TIMEOUT,
                        "Bounded execution exceeded its timeout.",
                        request.max_count,
                    )
                    break
                time.sleep(0.01)
            else:
                try:
                    if reply_file.stat().st_size > _MAX_REPLY_BYTES:
                        raise ValueError("bounded child evidence is too large")
                    with reply_file.open("rb") as reply:
                        payload = reply.read(_MAX_REPLY_BYTES + 1)
                    if len(payload) > _MAX_REPLY_BYTES:
                        raise ValueError("bounded child evidence changed size")
                    result = _decode_reply(payload, request)
                except (OSError, ValueError):
                    result = _failure(
                        AuthoringSystemDiagnosticCode.SERIALIZATION,
                        "Bounded child evidence could not be read safely.",
                        request.max_count,
                    )
        finally:
            if not _terminate_process_tree(process, input_thread, windows_job):
                result = (
                    _append_cleanup_failure(result, request.max_count)
                    if result is not None
                    else _failure(
                        AuthoringSystemDiagnosticCode.CLEANUP,
                        "Bounded process tree could not be terminated and reaped.",
                        request.max_count,
                    )
                )
        assert result is not None
        return result
