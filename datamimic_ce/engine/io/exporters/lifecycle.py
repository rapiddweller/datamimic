"""IO-owned completion and cleanup for buffered exports."""

import shutil
from pathlib import Path

from datamimic_ce.engine.io.exporters.core.exporter_context import ExporterContext
from datamimic_ce.engine.io.exporters.core.unified_buffered_exporter import ExporterError, UnifiedBufferedExporter
from datamimic_ce.engine.io.exporters.registry import create_exporter_list
from datamimic_ce.errors import ExternalFailureCause, IssueCode, export_config_error, is_user_error


def _buffered_exporters(
    setup_context: ExporterContext,
    product_name: str,
    export_uri: str | None,
    targets: list[str],
) -> list[UnifiedBufferedExporter]:
    _, without_operation = create_exporter_list(setup_context, product_name, export_uri, targets)
    return [exporter for exporter in without_operation if isinstance(exporter, UnifiedBufferedExporter)]


def finalize_exporter_chunks(
    setup_context: ExporterContext,
    product_name: str,
    export_uri: str | None,
    targets: list[str],
    worker_ids: range,
) -> None:
    """Finalize every worker's chunks before any artifact is published."""
    for exporter in _buffered_exporters(setup_context, product_name, export_uri, targets):
        for worker_id in worker_ids:
            try:
                exporter.finalize_chunks(worker_id)
            except Exception as error:
                if is_user_error(error):
                    raise
                raise export_config_error(code=IssueCode.EXPORT_FLUSH_FAILED, detail=type(error).__name__) from error


def publish_exported_artifacts(
    setup_context: ExporterContext,
    product_name: str,
    export_uri: str | None,
    targets: list[str],
) -> None:
    """Publish only after Runtime completes the separate finalization pass."""
    for exporter in _buffered_exporters(setup_context, product_name, export_uri, targets):
        exporter.save_exported_result()


def cleanup_exporter_chunks(descriptor_dir: Path, task_id: str) -> None:
    for temp_dir in descriptor_dir.glob(f"temp_result_{task_id}*"):
        shutil.rmtree(temp_dir)


def normalize_exporter_error_cause_for_transport(error: BaseException) -> None:
    """Normalize exporter-owned causes only in the private worker's transport edition."""
    current = error
    seen = {id(error)}
    while current.__cause__ is not None:
        cause = current.__cause__
        if id(cause) in seen:
            return
        seen.add(id(cause))
        if isinstance(cause, ExporterError):
            cause_types: list[str] = []
            nested: BaseException | None = cause
            nested_seen: set[int] = set()
            while nested is not None and id(nested) not in nested_seen and len(cause_types) < 16:
                nested_seen.add(id(nested))
                cause_types.append(f"{type(nested).__module__}.{type(nested).__name__}")
                nested = nested.__cause__
            object.__setattr__(current, "__cause__", ExternalFailureCause(cause_types[0], tuple(cause_types)))
            return
        current = cause
