# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

"""Pure scaffold verification policy over typed bounded-run evidence."""

from datamimic_ce.authoring.contracts import (
    MAX_DRY_RUN_COUNT,
    CaptureStatus,
    CompilePlan,
    DeterministicReplayEvidence,
    GeneratedProductCompilePlan,
    ReplayMismatchKind,
    ReplayProductMismatch,
    RetryWithParameterRemediation,
    ScaffoldVerification,
    ScaffoldVerificationEvidence,
    SmokeExportEvidence,
    SourceProductCompilePlan,
    TimeSeriesProductCompilePlan,
    VerificationGateStatus,
)
from datamimic_ce.authoring.dryrun import CapturedProducts, CapturedRun, SmokeExportCapture


def max_count_remediations(
    plan: CompilePlan,
    captured: CapturedProducts,
) -> list[RetryWithParameterRemediation]:
    """Derive one retry action from typed, statically bounded cap evidence."""

    products_by_name = {product.name: product for product in plan.products}
    minimums: dict[str, int] = {}
    for product in captured.products:
        evidence = product.capture
        planned = products_by_name.get(product.name)
        if (
            evidence is None
            or evidence.status is not CaptureStatus.CAPPED
            or evidence.requested is None
            or planned is None
        ):
            continue
        if isinstance(planned, GeneratedProductCompilePlan):
            minimum = planned.count_per_parent or planned.static_count
        elif isinstance(planned, TimeSeriesProductCompilePlan):
            minimum = planned.series_count
        elif isinstance(planned, SourceProductCompilePlan):
            minimum = evidence.requested
        else:
            continue
        if minimum > captured.max_count:
            minimums[product.name] = minimum
    if not minimums:
        return []
    required_minimum = max(minimums.values())
    if required_minimum > MAX_DRY_RUN_COUNT:
        return []

    captured_names = {product.name for product in captured.products}
    affected = set(minimums)
    changed = True
    while changed:
        changed = False
        for relationship in plan.relationships:
            if (
                relationship.parent in affected
                and relationship.child in captured_names
                and relationship.child not in affected
            ):
                affected.add(relationship.child)
                changed = True
    return [
        RetryWithParameterRemediation(
            minimum_value=required_minimum,
            affected_products=tuple(product.name for product in plan.products if product.name in affected),
        )
    ]


def blocked_verification(
    options: ScaffoldVerification,
    reason: str,
) -> ScaffoldVerificationEvidence:
    """Project requested gates that an earlier application stage prevented."""

    return ScaffoldVerificationEvidence(
        smoke_export=(
            SmokeExportEvidence(
                status=VerificationGateStatus.BLOCKED,
                reason=reason,
            )
            if options.smoke_export
            else SmokeExportEvidence()
        ),
        deterministic_replay=blocked_replay(options, reason),
    )


def blocked_replay(
    options: ScaffoldVerification,
    reason: str,
) -> DeterministicReplayEvidence:
    """Project replay as blocked only when it was requested."""

    if not options.deterministic_replay:
        return DeterministicReplayEvidence()
    return DeterministicReplayEvidence(
        status=VerificationGateStatus.BLOCKED,
        reason=reason,
    )


def replay_not_requested() -> DeterministicReplayEvidence:
    """Return canonical evidence for an omitted replay gate."""

    return DeterministicReplayEvidence()


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
        reason = "Not every applicable file exporter received captured rows"
    else:
        status = VerificationGateStatus.PASSED
        reason = "Every applicable file exporter accepted the captured rows"
    return SmokeExportEvidence(
        status=status,
        applicable_exporters=capture.applicable_exporters,
        attempted_exporters=capture.attempted_exporters,
        failed_exporters=capture.failed_exporters,
        reason=reason,
    )


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
                if first_row != replay_row
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
        reason="Deterministic replay requires an explicit seed in model.dm.json",
    )


def replay_evidence(
    first_run: CapturedRun,
    replay_run: CapturedRun,
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


__all__ = [
    "blocked_replay",
    "blocked_verification",
    "compare_captures",
    "replay_evidence",
    "replay_not_requested",
    "smoke_export_evidence",
    "unseeded_replay_evidence",
]
