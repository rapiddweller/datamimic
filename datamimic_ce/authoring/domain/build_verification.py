# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Optional verification gates over the same complete first capture."""

from .capture import CapturedProducts, CaptureValue, SmokeExportCapture
from .proof import (
    BuildVerificationEvidence,
    BuildVerificationOptions,
    DeterministicReplayEvidence,
    ReplayMismatchKind,
    ReplayProductMismatch,
    SmokeExportEvidence,
    VerificationGateStatus,
)
from .requests import BoundedExecutionEvidence


def smoke_export_evidence(
    requested: bool,
    capture: SmokeExportCapture,
) -> SmokeExportEvidence:
    """Project typed internal smoke facts without inspecting diagnostics."""

    if not requested:
        return SmokeExportEvidence()
    if not capture.requested:
        return SmokeExportEvidence(
            status=VerificationGateStatus.BLOCKED,
            reason="The bounded run ended before smoke export could execute",
        )
    if capture.applicable_exporters == 0:
        return SmokeExportEvidence(
            status=VerificationGateStatus.NOT_APPLICABLE,
            reason="The compiled model has no applicable file exporters",
        )
    if capture.failed_exporters > 0:
        status = VerificationGateStatus.FAILED
        reason = "One or more applicable file exporters failed"
    elif capture.attempted_exporters != capture.applicable_exporters:
        status = VerificationGateStatus.FAILED
        reason = "Not every applicable file exporter wrote the captured rows"
    else:
        status = VerificationGateStatus.PASSED
        reason = "Every applicable file exporter wrote all captured rows"
    return SmokeExportEvidence(
        status=status,
        applicable_exporters=capture.applicable_exporters,
        attempted_exporters=capture.attempted_exporters,
        failed_exporters=capture.failed_exporters,
        reason=reason,
    )


def _same_value(first: CaptureValue, replay: CaptureValue) -> bool:
    if type(first) is not type(replay):
        return False
    if isinstance(first, dict) and isinstance(replay, dict):
        return first.keys() == replay.keys() and all(_same_value(value, replay[key]) for key, value in first.items())
    if isinstance(first, list | tuple) and isinstance(replay, list | tuple):
        return len(first) == len(replay) and all(
            _same_value(left, right) for left, right in zip(first, replay, strict=True)
        )
    return first == replay


def compare_captures(
    first: CapturedProducts,
    replay: CapturedProducts,
) -> tuple[ReplayProductMismatch, ...]:
    """Compare all bounded rows without response samples or XML reconstruction."""

    first_products = {product.name: product for product in first.products}
    replay_products = {product.name: product for product in replay.products}
    mismatches: list[ReplayProductMismatch] = []

    for name in sorted(first_products.keys() - replay_products.keys()):
        mismatches.append(
            ReplayProductMismatch(
                product=name,
                kind=ReplayMismatchKind.MISSING_PRODUCT,
                first_count=len(first_products[name].rows),
                replay_count=0,
            )
        )
    for name in sorted(replay_products.keys() - first_products.keys()):
        mismatches.append(
            ReplayProductMismatch(
                product=name,
                kind=ReplayMismatchKind.UNEXPECTED_PRODUCT,
                first_count=0,
                replay_count=len(replay_products[name].rows),
            )
        )
    for name in sorted(first_products.keys() & replay_products.keys()):
        first_rows = first_products[name].rows
        replay_rows = replay_products[name].rows
        first_difference = next(
            (
                index
                for index, (first_row, replay_row) in enumerate(zip(first_rows, replay_rows, strict=False))
                if not _same_value(first_row, replay_row)
            ),
            None,
        )
        if first_difference is not None:
            mismatches.append(
                ReplayProductMismatch(
                    product=name,
                    kind=ReplayMismatchKind.ROW_CONTENT,
                    first_count=len(first_rows),
                    replay_count=len(replay_rows),
                    first_difference=first_difference,
                )
            )
        elif len(first_rows) != len(replay_rows):
            mismatches.append(
                ReplayProductMismatch(
                    product=name,
                    kind=ReplayMismatchKind.ROW_COUNT,
                    first_count=len(first_rows),
                    replay_count=len(replay_rows),
                    first_difference=min(len(first_rows), len(replay_rows)),
                )
            )
    return tuple(mismatches)


def unseeded_replay_evidence() -> DeterministicReplayEvidence:
    """Fail a requested deterministic claim whose explicit seed is absent."""

    return DeterministicReplayEvidence(
        status=VerificationGateStatus.FAILED,
        reason="Deterministic replay requires an explicit rngSeed in the descriptor",
    )


def replay_evidence(
    first_run: BoundedExecutionEvidence,
    replay_run: BoundedExecutionEvidence,
) -> DeterministicReplayEvidence:
    """Evaluate a service-supplied second run without performing any I/O."""

    if not replay_run.base_run_ok:
        return DeterministicReplayEvidence(
            status=VerificationGateStatus.FAILED,
            reason="The replay execution did not complete successfully",
        )
    mismatches = compare_captures(first_run.captured, replay_run.captured)
    compared_products = len(first_run.captured.products)
    compared_rows = sum(len(product.rows) for product in first_run.captured.products)
    if mismatches:
        return DeterministicReplayEvidence(
            status=VerificationGateStatus.FAILED,
            mismatches=mismatches,
            compared_products=compared_products,
            compared_rows=compared_rows,
            reason="The replay differs from the first full bounded capture",
        )
    return DeterministicReplayEvidence(
        status=VerificationGateStatus.PASSED,
        compared_products=compared_products,
        compared_rows=compared_rows,
        reason="The full bounded capture is identical across both seeded runs",
    )


def blocked_verification(options: BuildVerificationOptions, reason: str) -> BuildVerificationEvidence:
    return BuildVerificationEvidence(
        smoke_export=(
            SmokeExportEvidence(status=VerificationGateStatus.BLOCKED, reason=reason)
            if options.smoke_export
            else SmokeExportEvidence()
        ),
        deterministic_replay=(
            DeterministicReplayEvidence(status=VerificationGateStatus.BLOCKED, reason=reason)
            if options.deterministic_replay
            else DeterministicReplayEvidence()
        ),
    )
