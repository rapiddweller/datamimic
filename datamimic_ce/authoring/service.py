# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Service layer for scaffold operations.

Single implementation used by both MCP (datamimic_scaffold) and CLI
(datamimic scaffold) — eliminates drift between transports.
"""

from datamimic_ce.authoring.contracts import ProductResult, ScaffoldRequest, ScaffoldResult
from datamimic_ce.authoring.diagnostics import _diagnostic_dicts


def scaffold(request: ScaffoldRequest) -> ScaffoldResult:
    """Render a compact JSON spec to DATAMIMIC DSL, lint, optionally dry-run.

    Calls the scaffold.check() pipeline and maps ScaffoldCheckResult into
    ScaffoldResult with full fidelity (products with samples, diagnostics,
    normalization notes).

    Args:
        request: ScaffoldRequest with spec, dry_run, max_count, sample_rows, response_format

    Returns:
        ScaffoldResult with ok, stage, xml, diagnostics, products, normalization_notes
    """
    from datamimic_ce.authoring.scaffold import check

    check_result = check(
        request.spec,
        dry_run=request.dry_run,
        max_count=request.max_count,
        sample_rows=request.sample_rows,
    )

    # Render failed — error stage
    if check_result.stage == "render":
        return ScaffoldResult(
            ok=False,
            stage="render",
            xml=None,
            error=check_result.render_error,
            summary=None,
            diagnostics=[],
            truncated=False,
            products=[],
            normalization_notes=list(check_result.normalization_notes),
        )

    # Lint stage — may fail or succeed
    if check_result.stage == "lint":
        lint_result = check_result.lint_result
        diagnostics = _diagnostic_dicts(
            lint_result.diagnostics,
            detailed=(request.response_format == "detailed"),
        )
        return ScaffoldResult(
            ok=lint_result.ok,
            stage="lint",
            xml=check_result.xml,
            error=None,
            summary=lint_result.summary() if lint_result else None,
            diagnostics=diagnostics,
            truncated=lint_result.truncated if lint_result else False,
            products=[],
            normalization_notes=list(check_result.normalization_notes),
        )

    # Dry-run stage
    dr = check_result.dryrun_result
    diagnostics = _diagnostic_dicts(
        dr.diagnostics,
        detailed=(request.response_format == "detailed"),
    )
    products = [
        ProductResult(
            name=p.name,
            count=p.count,
            sample=p.sample,
            truncated_rows=p.truncated_rows,
        )
        for p in dr.products
    ]

    return ScaffoldResult(
        ok=dr.ok,
        stage="dry_run",
        xml=check_result.xml,
        error=None,
        summary=None,
        diagnostics=diagnostics,
        truncated=False,
        products=products,
        normalization_notes=list(check_result.normalization_notes),
    )
