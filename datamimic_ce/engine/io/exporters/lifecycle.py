"""IO-owned completion and cleanup for buffered exports."""

import shutil
from pathlib import Path

from datamimic_ce.engine.io.exporters.core.exporter_context import ExporterContext
from datamimic_ce.engine.io.exporters.core.unified_buffered_exporter import UnifiedBufferedExporter
from datamimic_ce.engine.io.exporters.registry import create_exporter_list


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
            exporter.finalize_chunks(worker_id)


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
