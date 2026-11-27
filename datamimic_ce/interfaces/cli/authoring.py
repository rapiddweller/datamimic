"""File/stdin transport for the typed Authoring application."""

from __future__ import annotations

import re
import sys
from pathlib import Path, PurePosixPath
from typing import Annotated

import typer
from pydantic import ValidationError

from datamimic_ce.authoring import create_authoring_application
from datamimic_ce.authoring.adapters.workspace import init_project
from datamimic_ce.authoring.domain.capabilities import CapabilityDomain
from datamimic_ce.authoring.domain.dm_json import DmJsonDocumentV1
from datamimic_ce.authoring.domain.project_run import ProjectParam, ProjectRunRequest, ProjectRunResult
from datamimic_ce.authoring.domain.project_scaffold import ProjectPattern
from datamimic_ce.authoring.domain.requests import (
    PROJECT_ENTRY_PATH,
    AuthoringSchemaId,
    CompileDocumentRequest,
    DecompileDocumentRequest,
    LintRequest,
    LintResult,
    ReadyCompileDocument,
    ReadyDecompileDocument,
    ReferenceRequest,
    ReferenceTopic,
    RejectedBuild,
    RejectedCompileDocument,
    RejectedDecompileDocument,
    RunPhase,
    RunRequest,
    RunResult,
)
from datamimic_ce.domains.api import get_datamimic_lib_version
from datamimic_ce.interfaces.cli.presenter import NEXT_STEP_HINT, CliOutputFormat, build_exit_code, emit_authoring

app = typer.Typer(no_args_is_help=True, help="Compile, inspect and verify DATAMIMIC descriptors.")
OutputFormat = Annotated[CliOutputFormat, typer.Option("--format", "-f")]
Input = Annotated[str, typer.Argument(help="UTF-8 input file; '-' reads stdin.")]
DescriptorPath = Annotated[
    str | None,
    typer.Option(
        "--descriptor-path",
        help="Workspace-relative path of the descriptor; default 'model.xml' for stdin, else the file's own path.",
    ),
]
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


def _descriptor_path(source: str, workspace_root: Path | None, override: str | None = None) -> PurePosixPath:
    if override is not None:
        return PurePosixPath(override)
    if source == "-":
        return PurePosixPath("model.xml")
    return PurePosixPath(Path(source).resolve().relative_to(_workspace(source, workspace_root).resolve()).as_posix())


@app.command("version", help="Show the CE version, Python version, git commit (git install only) and Build protocol.")
def version(output_format: OutputFormat = CliOutputFormat.JSON) -> None:
    emit_authoring(create_authoring_application().version(), output_format)


@app.command("schema", help="Show an authoring schema; defaults to the DM JSON document schema.")
def schema(
    name: Annotated[AuthoringSchemaId, typer.Option("--name")] = AuthoringSchemaId.DM_JSON_DOCUMENT_V1,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    emit_authoring(create_authoring_application().schema(name), output_format)


@app.command("capabilities", help="List DSL capabilities; use --full for their contracts.")
def capabilities(
    full: Annotated[bool, typer.Option("--full")] = False,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    snapshot = create_authoring_application().capabilities()
    emit_authoring(snapshot.to_dict() if full else snapshot.to_index_dict(), output_format)


@app.command("capability", help="Inspect one DSL capability by domain and name.")
def capability(
    domain: Annotated[CapabilityDomain, typer.Option("--domain")],
    name: Annotated[str, typer.Option("--name")],
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    result = create_authoring_application().capability(domain, name)
    emit_authoring(result, output_format, exit_code=0 if result.ok else 1)


@app.command(
    "reference",
    help="Read guidance by topic, starting with overview. Data files: --topic learning --name data_files.",
)
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


@app.command("compile", help="Compile a DM JSON document to XML; this does not prove the project.")
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


@app.command("decompile", help="Decompile XML to DM JSON; this does not prove the project.")
def decompile_document(
    source: Input,
    descriptor_path: DescriptorPath = None,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    try:
        logical_path = _descriptor_path(source, workspace_root, descriptor_path)
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
    project: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=False,
            readable=True,
            help="Project directory holding datamimic.xml and acceptance/build.json.",
        ),
    ] = Path("."),
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    """Prove a project: its datamimic.xml entry and steps against its acceptance/build.json.

    Only outcome ready is a clean proof. Outcome ready_with_gaps passed the run but has open coverage
    gaps: see action_required and the coverage_gap warnings, and fix every one before you report success.

    \b
    Exit code 0: ready. Exit code 3: ready_with_gaps.
    Exit code 1: rejected, or input that Build cannot read.
    JSON evidence can include sample row values; do not share transcripts of real data.
    """
    application = create_authoring_application(workspace_root=project, descriptor_path=PROJECT_ENTRY_PATH)
    result = application.build()
    emit_authoring(result, output_format, exit_code=build_exit_code(result))


@app.command("run-project")
def run_project(
    project: Annotated[
        Path,
        typer.Argument(exists=True, file_okay=False, readable=True, help="Project directory holding datamimic.xml."),
    ] = Path("."),
    allow_side_effects: Annotated[
        bool,
        typer.Option(
            "--allow-side-effects",
            help="Allow effects outside the project; local output/ files are written without this option.",
        ),
    ] = False,
    params: Annotated[
        list[str] | None, typer.Option("--param", help="Runtime property NAME=VALUE; repeatable.")
    ] = None,
    timeout: Annotated[int, typer.Option("--timeout")] = 600,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    """Build the project, then run it for its real data.

    A completed run can exit code 0 even when build_outcome is ready_with_gaps.
    Inspect action_required and fix the gaps before reporting a clean proof.
    """
    try:
        pairs = [re.split("=", item, maxsplit=1) for item in params or []]
        if any(len(pair) != 2 for pair in pairs):
            raise ValueError("--param needs NAME=VALUE")
        request = ProjectRunRequest(
            allow_side_effects=allow_side_effects,
            params=tuple(ProjectParam(name=pair[0], value=pair[1]) for pair in pairs),
            timeout_seconds=timeout,
        )
    except (ValueError, ValidationError):
        emit_authoring(
            ProjectRunResult.from_input_error("Run options are invalid: check --param NAME=VALUE and --timeout."),
            output_format,
            exit_code=1,
        )
    application = create_authoring_application(workspace_root=project, descriptor_path=PROJECT_ENTRY_PATH)
    result = application.run_project(request)
    emit_authoring(result, output_format, exit_code=0 if result.outcome == "completed" else 1)


@app.command("init")
def init(
    project: Annotated[
        Path,
        typer.Argument(metavar="PROJECT", help="Directory for the new project; it is created when it is missing."),
    ] = Path("."),
    pattern: Annotated[
        ProjectPattern,
        typer.Option("--pattern", help="Starter project; each one is ready as written."),
    ] = ProjectPattern.FLAT,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    """Write a starter project (datamimic.xml and acceptance/build.json) that Build accepts. Never overwrites."""
    application = create_authoring_application()
    result = init_project(project, application.scaffold(pattern))
    exit_code = 1 if result.outcome == "not_written" else 0
    if output_format is CliOutputFormat.JSON:
        emit_authoring(result, output_format, exit_code=exit_code)
    if exit_code:
        typer.echo(f"Init failed: {result.diagnostics[0].message}", err=True)
        raise typer.Exit(code=exit_code)
    typer.echo(f"Wrote the {pattern.value} project to {project}: {', '.join(result.files)}")
    typer.echo(NEXT_STEP_HINT)


@app.command("lint", help="Validate an XML descriptor without executing it.")
def lint(
    source: Input,
    descriptor_path: DescriptorPath = None,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    try:
        logical_path = _descriptor_path(source, workspace_root, descriptor_path)
        request = LintRequest(xml=_read(source))
        # Builds the application inside the handler: it rejects an invalid descriptor path.
        application = create_authoring_application(
            workspace_root=_workspace(source, workspace_root), descriptor_path=logical_path
        )
    except (ValueError, ValidationError) as error:
        emit_authoring(
            LintResult.from_input_error(_input_message(error, "Invalid or unreadable XML input or descriptor path.")),
            output_format,
            exit_code=1,
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
    descriptor_path: str | None,
    *,
    dry: bool,
) -> None:
    try:
        logical_path = _descriptor_path(source, workspace_root, descriptor_path)
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
            RunResult.from_input_error(
                _input_message(error, "Invalid XML input or bounded-run options."),
                RunPhase.DRY_RUN if dry else RunPhase.RUN,
            ),
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
    descriptor_path: DescriptorPath = None,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    """Dry-run bounded XML with side effects disabled, without reading acceptance/build.json.

    The default --max-count is 10, independent of the project's Build limit.
    JSON output can include sample row values; do not share transcripts of real data.
    """
    _run(source, workspace_root, output_format, max_count, sample_rows, timeout, False, descriptor_path, dry=True)


@app.command("run")
def bounded_run(
    source: Input,
    max_count: Annotated[int, typer.Option("--max-count")] = 10,
    sample_rows: Annotated[int, typer.Option("--sample-rows")] = 5,
    timeout: Annotated[int, typer.Option("--timeout")] = 30,
    allow_side_effects: Annotated[bool, typer.Option("--allow-side-effects")] = False,
    descriptor_path: DescriptorPath = None,
    workspace_root: WorkspaceRoot = None,
    output_format: OutputFormat = CliOutputFormat.JSON,
) -> None:
    """Run bounded XML with optional side effects, without reading acceptance/build.json.

    The default --max-count is 10, independent of the project's Build limit.
    JSON output can include sample row values; do not share transcripts of real data.
    """
    _run(
        source,
        workspace_root,
        output_format,
        max_count,
        sample_rows,
        timeout,
        allow_side_effects,
        descriptor_path,
        dry=False,
    )


@app.command("export-contract", help="Write the authoring contract bundle to the specified path.")
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
