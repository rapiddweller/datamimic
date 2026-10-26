# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Private workspace and process ownership for one bounded CE execution."""

from __future__ import annotations

import os
import pickle
import signal
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from hashlib import sha256
from itertools import islice
from pathlib import Path, PurePosixPath

from lxml import etree

from datamimic_ce.authoring.adapters import dryrun
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
    ProjectFileDigest,
    SourceAccessEvidence,
)
from datamimic_ce.errors import DescriptorLocation, DomainError, GeneratorConfigError, IssueCode, UserErrorBase
from datamimic_ce.errors.catalog import get_issue_definition
from datamimic_ce.errors.codes import ErrorCode

_MAX_WORKSPACE_BYTES = 256 * 1024 * 1024
_MAX_WORKSPACE_FILE_BYTES = MAX_RESOURCE_BYTES
_MAX_WORKSPACE_FILES = 2_000
_MAX_WORKSPACE_ENTRIES = 4_000
_MAX_WORKSPACE_DEPTH = 64
_MAX_REPLY_BYTES = dryrun._MAX_WORKER_REPLY_BYTES


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


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> None:
    """Kill the private POSIX group, or use Windows' descendant-aware taskkill."""
    if os.name == "nt":
        completed = subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=2, check=False
        )
        if completed.returncode != 0:
            raise OSError("taskkill did not terminate the bounded process tree")
    else:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        with suppress(subprocess.TimeoutExpired):
            process.wait(timeout=0.2)
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired as error:
        raise OSError("bounded worker did not stop") from error


def _read_file_digests(
    paths: tuple[str, ...], request: BoundedExecutionRequest, workspace: Path
) -> tuple[ProjectFileDigest, ...]:
    """Hash each file the child read from the private copy; the run could not change those files."""
    private = AuthoringWorkspaceContext(workspace, request.descriptor_path)
    digests = []
    for path in paths:
        relative = PurePosixPath(path)
        digests.append(
            ProjectFileDigest(
                path=relative,
                sha256=sha256(private.read_resource_bytes(private.resolve_descriptor_path(relative))).hexdigest(),
            )
        )
    return tuple(digests)


# Whole-value ``{name}`` is replaced by a property, possibly a secret, when the runtime parses the descriptor; ``__``
# is the interpolation mark of string and pattern. A message with neither mark is the literal text of the file.
_INTERPOLATION_MARKS = ("{", "}", "__")


def _failed_assert(
    location: DescriptorLocation, request: BoundedExecutionRequest, entry: str, workspace: Path
) -> tuple[tuple[str | int, ...], str, str | None]:
    """Path, message and literal rule text of the failed <assert>, read from the raw file that ran. Only the
    attribute text of that file can prove a message literal: the runtime value of ``{name}`` has no braces."""
    from datamimic_ce.engine.dsl.api import parse_xml_source

    file = location.descriptor_path or entry
    path: tuple[str | int, ...] = ("descriptor", entry) if file == entry else ("include", file)
    line: tuple[str | int, ...] = () if location.line is None else ("line", location.line)
    private = AuthoringWorkspaceContext(workspace, request.descriptor_path)
    # (message attribute, name of the enclosing generate or nestedKey) of each assert on the reported line
    found: list[tuple[str | None, str | None]] = []
    owners: list[str | None] = []
    try:
        root = parse_xml_source(request.xml if file == entry else private.read_project_file(PurePosixPath(file)))
        for event, item in etree.iterwalk(root, events=("start", "end")):
            if item.tag in ("generate", "nestedKey"):
                owners = [*owners, item.get("name")] if event == "start" else owners[:-1]
            elif event == "start" and item.tag == "assert" and item.sourceline == location.line:
                found.append((item.get("message"), owners[-1] if owners else None))
    except (OSError, ValueError, etree.XMLSyntaxError):
        found = []
    if len(found) != 1 or location.line is None:
        return (*path, "assert", *line), "An <assert> failed.", None
    raw, owner = found[0]
    where = "under <setup>" if owner is None else f"in '{owner}'"
    rule = raw if raw and not any(mark in raw for mark in _INTERPOLATION_MARKS) else None
    message = (
        f"The <assert> {where} failed: {rule}"
        if rule is not None
        else f"The <assert> {where} failed. It has no message; a message names the rule."
        if raw is None
        else f"The <assert> {where} failed. Its message is not shown: it contains {{, }} or __ and can hold a "
        "property value."
    )
    return (*path, "assert", *line), message, rule


def _decode_reply(payload: bytes, request: BoundedExecutionRequest, workspace: Path) -> BoundedExecutionEvidence:
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
            entry = request.descriptor_path.as_posix()
            if (
                location is not None
                and isinstance(message.error, UserErrorBase)
                and message.error.issue_code is IssueCode.TASK_ASSERT_FAILED
            ):
                assert_path, text, rule = _failed_assert(location, request, entry, workspace)
                return BoundedExecutionEvidence(
                    ok=False,
                    captured=(
                        dryrun._captured_products(message.stopped_capture, request.max_count)
                        if message.stopped_capture is not None
                        else CapturedProducts((), request.max_count)
                    ),
                    diagnostics=(
                        Diagnostic(
                            code=AuthoringSystemDiagnosticCode.ASSERT_FAILED,
                            phase=DiagnosticPhase.EVIDENCE,
                            message=text,
                            remediation="Change the data or the model so that every row meets the condition, or "
                            "correct the condition. The run stops at the first failed <assert>, as datamimic run does.",
                            ce_error=identity,
                            path=assert_path,
                            expected=rule,
                        ),
                    ),
                    base_run_ok=False,
                    stopped_by_assert=True,
                )
            definition = (
                get_issue_definition(message.error.issue_code)
                if isinstance(message.error, UserErrorBase) and message.error.issue_code is not None
                else None
            )
            path: tuple[str, ...] = message.policy_path or ("descriptor", entry)
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
            # The limit is Build's own number, so the message can name it.
            over_limit = (
                isinstance(message.error, UserErrorBase)
                and message.error.issue_code is IssueCode.TASK_TOTAL_ROW_BUDGET_EXCEEDED
            )
            reason = (
                f"The generated rows of all products together exceed the Build limit {request.max_count}."
                if over_limit
                else constructor_reason
            )
            diagnostic = Diagnostic(
                code=AuthoringRuleId.SIDE_EFFECT
                if message.policy_refusal
                else AuthoringSystemDiagnosticCode.CHILD_EXECUTION,
                phase=DiagnosticPhase.POLICY if message.policy_refusal else DiagnosticPhase.EVIDENCE,
                message=(
                    reason
                    if reason is not None
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
                expected=request.max_count if over_limit else None,
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
        # A side-effect run of a clear or drop succeeded when the engine raised nothing; it captures no rows.
        ran_operation = bool(message.executed_operations)
        # A skipped clear or drop is reported, not failed: bounded execution neither ran it nor proves its effect.
        skipped: tuple[Diagnostic, ...] = ()
        for name in message.skipped_operations:
            skipped += (
                Diagnostic(
                    code=AuthoringSystemDiagnosticCode.NOT_EXECUTED,
                    phase=DiagnosticPhase.EVIDENCE,
                    severity="warning",
                    message=(
                        f"'{name}' is a destructive database operation (clear or drop); bounded execution did not "
                        "run it, so its effect is not proved."
                    ),
                    remediation=(
                        "Run it with authoring run --allow-side-effects or datamimic run against the target, and "
                        "check the database state there."
                    ),
                ),
            )
        if not base_run_ok and (captured.products or not (skipped or ran_operation)):
            diagnostics += (
                Diagnostic(
                    code=AuthoringSystemDiagnosticCode.NOT_EXECUTED,
                    phase=DiagnosticPhase.EVIDENCE,
                    message="Bounded execution produced no captured rows.",
                    remediation="Use a descriptor that produces the required bounded data.",
                ),
            )
        return BoundedExecutionEvidence(
            ok=(base_run_ok or bool(skipped) or ran_operation) and not diagnostics,
            captured=captured,
            diagnostics=diagnostics + skipped,
            smoke_export=message.smoke_export,
            source_accesses=tuple(
                SourceAccessEvidence(source_type=source_type, requests=count)
                for source_type, count in message.source_accesses
            ),
            # A run that only skipped clear/drop has nothing to capture and nothing failed. A product without rows
            # next to a skipped clear stays a failure, as without the clear; Build still needs products.
            base_run_ok=base_run_ok or ((bool(skipped) or ran_operation) and not captured.products),
            files=_read_file_digests(message.read_files, request, workspace),
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

    def execute(self, request: BoundedExecutionRequest) -> BoundedExecutionEvidence:
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
                result = self._execute_child(request, private_workspace, request_file, private_root / "reply.pickle")
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
        request: BoundedExecutionRequest, workspace: Path, request_file: Path, reply_file: Path
    ) -> BoundedExecutionEvidence:
        command = [
            sys.executable,
            "-P",
            "-m",
            "datamimic_ce.authoring.adapters.bounded_executor_child",
            str(request_file),
            str(reply_file),
            str(workspace),
        ]
        try:
            process = subprocess.Popen(
                command,
                env=None if request.hash_seed is None else {**os.environ, "PYTHONHASHSEED": str(request.hash_seed)},
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=os.name == "posix",
            )
        except OSError:
            return _failure(
                AuthoringSystemDiagnosticCode.CHILD_CRASH, "Bounded child could not start.", request.max_count
            )
        result: BoundedExecutionEvidence
        deadline = time.monotonic() + request.timeout_seconds
        try:
            while not reply_file.exists():
                if process.poll() is not None:
                    result = _failure(
                        AuthoringSystemDiagnosticCode.CHILD_CRASH,
                        f"Bounded child exited without evidence (exit code {process.returncode}).",
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
                    result = _decode_reply(payload, request, workspace)
                except (OSError, ValueError):
                    result = _failure(
                        AuthoringSystemDiagnosticCode.SERIALIZATION,
                        "Bounded child evidence could not be read safely.",
                        request.max_count,
                    )
        finally:
            try:
                _terminate_process_tree(process)
            except (OSError, subprocess.TimeoutExpired):
                result = _failure(
                    AuthoringSystemDiagnosticCode.CLEANUP,
                    "Bounded process tree could not be terminated and reaped.",
                    request.max_count,
                )
        return result
