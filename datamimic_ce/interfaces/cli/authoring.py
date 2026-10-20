"""File/stdin transport for the typed Authoring application."""

from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath
from typing import Annotated

import typer
from pydantic import ValidationError

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.requests import (
    AuthoringSchemaId,
    BuildRequestV4,
    CompileDocumentRequest,
    DecompileDocumentRequest,
    LintRequest,
    LintResult,
    ReadyBuild,
    ReadyCompileDocument,
    ReadyDecompileDocument,
    ReferenceRequest,
    ReferenceTopic,
    RejectedBuild,
    RejectedCompileDocument,
    RejectedDecompileDocument,
    RunRequest,
    RunResult,
)
from datamimic_ce.domains.api import get_datamimic_lib_version
from datamimic_ce.interfaces.cli.presenter import CliOutputFormat, emit_authoring

app = typer.Typer(no_args_is_help=True, help="Compile, inspect and verify DATAMIMIC descriptors.")
OutputFormat = Annotated[CliOutputFormat, typer.Option("--format", "-f")]
Input = Annotated[str, typer.Argument(help="UTF-8 input file; '-' reads stdin.")]
WorkspaceRoot = Annotated[
    Path | None,
    typer.Option(
        "--workspace-root",
        exists=True,
        file_okay=False,
        readable=True,
        resolve_path=True,
        help="Host-owned project directory.",
    ),
]


class _UnreadableInput(ValueError):
    """The input channel itself failed, as opposed to its content."""


def _read(source: str) -> str:
    try:
        return sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    # Only the file name is echoed: the host directory must not leak into diagnostics.
    except FileNotFoundError as error:
        raise _UnreadableInput(f"Input file not found: {Path(source).name}") from error
    except (OSError, UnicodeError) as error:
        raise _UnreadableInput(f"Input must be a readable UTF-8 file or '-': {Path(source).name}") from error


def _input_message(error: Exception, fallback: str) -> str:
    if isinstance(error, _UnreadableInput):
        return str(error)
    if isinstance(error, ValidationError):
        # Reuse the Build request projection (location and reason, never the input value).
        reasons = (item.message for item in RejectedBuild.from_model_validation(error).diagnostics[:3])
        return " ".join((fallback, *reasons))
    return fallback


def _workspace(source: str, workspace_root: Path | None = None) -> Path:
    return workspace_root or (Path.cwd() if source == "-" else Path(source).resolve().parent)


def _descriptor_path(source: str, workspace_root: Path | None) -> PurePosixPath:
    if source == "-":
        return PurePosixPath("model.xml")
    return PurePosixPath(Path(source).resolve().relative_to(_workspace(source, workspace_root).resolve()).as_posix())


@app.command("version")
def version(output_format: OutputFormat = CliOutputFormat.JSON) -> None:
    emit_authoring({"ce_version": get_datamimic_lib_version() or "unknown"}, output_format)


@app.command("schema")
def schema(
    name: Annotated[AuthoringSchemaId, typer.Option("--name")] = AuthoringSchemaId.DM_JSON_DOCUMENT_V1,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    emit_authoring(create_authoring_application().schema(name), output_format)


@app.command("capabilities")
def capabilities(
    full: Annotated[bool, typer.Option("--full")] = False,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    snapshot = create_authoring_application().capabilities()
    emit_authoring(snapshot.to_dict() if full else snapshot.to_index_dict(), output_format)


@app.command("capability")
def capability(
    domain: Annotated[CapabilityDomain, typer.Option("--domain")],
    name: Annotated[str, typer.Option("--name")],
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    result = create_authoring_application().capability(domain, name)
    emit_authoring(result, output_format, exit_code=0 if result.ok else 1)


@app.command("reference")
def reference(
    topic: Annotated[ReferenceTopic, typer.Option("--topic")] = ReferenceTopic.OVERVIEW,
    name: Annotated[str | None, typer.Option("--name")] = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    try:
        request = ReferenceRequest(topic=topic, name=name)
    except ValidationError:
        emit_authoring({"ok": False, "error": "Invalid reference request."}, output_format, exit_code=1)
    emit_authoring(create_authoring_application().reference(request), output_format)


@app.command("compile")
def compile_document(
    source: Input,
    descriptor_path: Annotated[str, typer.Option("--descriptor-path")] = "model.xml",
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    try:
        document = DmJsonDocumentV1.model_validate_json(_read(source))
        request = CompileDocumentRequest(document=document, descriptor_path=PurePosixPath(descriptor_path))
    except (ValueError, ValidationError) as error:
        emit_authoring(
            RejectedCompileDocument.from_input_error(
                _input_message(error, "Invalid DM JSON input or descriptor path.")
            ),
            output_format,
            exit_code=1,
        )
    application = create_authoring_application(
        workspace_root=_workspace(source, workspace_root), descriptor_path=request.descriptor_path
    )
    result = application.compile_document(request)
    emit_authoring(result, output_format, exit_code=0 if isinstance(result, ReadyCompileDocument) else 1)


@app.command("decompile")
def decompile_document(
    source: Input,
    descriptor_path: Annotated[str | None, typer.Option("--descriptor-path")] = None,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    try:
        logical_path = (
            PurePosixPath(descriptor_path) if descriptor_path is not None else _descriptor_path(source, workspace_root)
        )
        request = DecompileDocumentRequest(xml=_read(source), descriptor_path=logical_path)
    except (ValueError, ValidationError) as error:
        emit_authoring(
            RejectedDecompileDocument.from_input_error(_input_message(error, "Invalid XML input or descriptor path.")),
            output_format,
            exit_code=1,
        )
    application = create_authoring_application(
        workspace_root=_workspace(source, workspace_root), descriptor_path=request.descriptor_path
    )
    result = application.decompile_document(request)
    emit_authoring(result, output_format, exit_code=0 if isinstance(result, ReadyDecompileDocument) else 1)


@app.command("build")
def build(
    source: Input,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    try:
        request = BuildRequestV4.model_validate_json(_read(source))
    except ValidationError as error:
        emit_authoring(RejectedBuild.from_model_validation(error), output_format, exit_code=1)
    except ValueError as error:
        emit_authoring(
            RejectedBuild.from_input_error(_input_message(error, "Invalid or unreadable Build request.")),
            output_format,
            exit_code=1,
        )
    application = create_authoring_application(
        workspace_root=_workspace(source, workspace_root), descriptor_path=request.descriptor_path
    )
    result = application.build(request)
    emit_authoring(result, output_format, exit_code=0 if isinstance(result, ReadyBuild) else 1)


@app.command("lint")
def lint(
    source: Input,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    try:
        logical_path = _descriptor_path(source, workspace_root)
        request = LintRequest(xml=_read(source))
    except (ValueError, ValidationError) as error:
        emit_authoring(
            LintResult.from_input_error(_input_message(error, "Invalid or unreadable XML input.")),
            output_format,
            exit_code=1,
        )
    application = create_authoring_application(
        workspace_root=_workspace(source, workspace_root), descriptor_path=logical_path
    )
    result = application.lint(request)
    emit_authoring(result, output_format, exit_code=0 if result.ok else 1)


def _run(
    source: str,
    workspace_root: Path | None,
    output_format: CliOutputFormat,
    max_count: int,
    sample_rows: int,
    timeout: int,
    allow_side_effects: bool,
    *,
    dry: bool,
) -> None:
    try:
        logical_path = _descriptor_path(source, workspace_root)
        request = RunRequest(
            xml=_read(source),
            descriptor_path=logical_path,
            max_count=max_count,
            sample_rows=sample_rows,
            timeout_seconds=timeout,
            allow_side_effects=allow_side_effects,
        )
    except (ValueError, ValidationError) as error:
        emit_authoring(
            RunResult.from_input_error(_input_message(error, "Invalid XML input or bounded-run options.")),
            output_format,
            exit_code=1,
        )
    application = create_authoring_application(
        workspace_root=_workspace(source, workspace_root), descriptor_path=logical_path
    )
    result = application.dry_run(request) if dry else application.run(request)
    emit_authoring(result, output_format, exit_code=0 if result.ok else 1)


@app.command("dry-run")
def dry_run(
    source: Input,
    max_count: Annotated[int, typer.Option("--max-count")] = 10,
    sample_rows: Annotated[int, typer.Option("--sample-rows")] = 5,
    timeout: Annotated[int, typer.Option("--timeout")] = 30,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    _run(source, workspace_root, output_format, max_count, sample_rows, timeout, False, dry=True)


@app.command("run")
def bounded_run(
    source: Input,
    max_count: Annotated[int, typer.Option("--max-count")] = 10,
    sample_rows: Annotated[int, typer.Option("--sample-rows")] = 5,
    timeout: Annotated[int, typer.Option("--timeout")] = 30,
    allow_side_effects: Annotated[bool, typer.Option("--allow-side-effects")] = False,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    _run(source, workspace_root, output_format, max_count, sample_rows, timeout, allow_side_effects, dry=False)


@app.command("export-contract")
def export_contract(
    output: Annotated[Path, typer.Argument()],
    package_version: Annotated[str | None, typer.Option("--package-version")] = None,
    commit_sha: Annotated[str, typer.Option("--commit-sha")] = "local",
) -> None:
    from datamimic_ce.interfaces.bundle import write_contract_bundle

    path = write_contract_bundle(
        output, package_version=package_version or get_datamimic_lib_version() or "unknown", commit_sha=commit_sha
    )
    typer.echo(path)
