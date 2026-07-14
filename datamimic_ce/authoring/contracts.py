# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Canonical contracts and input limits for agent-facing authoring operations.

Single source of truth across MCP, CLI, and internal service layers.  Keeping
the shared numeric limits here prevents one transport from accepting requests
that another transport rejects.
"""

from typing import Any

from pydantic import BaseModel, Field

MIN_DIAGNOSTICS = 1
MAX_DIAGNOSTICS = 200
MIN_DRY_RUN_COUNT = 1
MAX_DRY_RUN_COUNT = 1000
MIN_SAMPLE_ROWS = 1
MAX_SAMPLE_ROWS = 50
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 120


class ScaffoldRequest(BaseModel):
    """Canonical request contract for scaffold operations."""

    spec: dict[str, Any] = Field(
        ...,
        description=(
            "Compact JSON spec conforming to SPEC_JSON_SCHEMA. Shape: "
            "{'seed': int?, 'generates': [{'name': str, 'count': int?, 'target': str, "
            "'source': str?, 'source_type': str?, 'fields': [...]}]}"
        ),
    )
    dry_run: bool = Field(
        True,
        description="Whether to also dry-run the rendered descriptor after a clean lint (default True)",
    )
    max_count: int = Field(
        10,
        ge=MIN_DRY_RUN_COUNT,
        le=MAX_DRY_RUN_COUNT,
        description="Per-<generate> record cap when dry_run=True (applies to nested generates too)",
    )
    sample_rows: int = Field(
        5,
        ge=MIN_SAMPLE_ROWS,
        le=MAX_SAMPLE_ROWS,
        description="Sample rows to capture per product during dry-run",
    )
    response_format: str = Field(
        "concise",
        pattern="^(concise|detailed)$",
        description="Response format: concise (key diagnostics) or detailed (full diagnostic info)",
    )


class ProductResult(BaseModel):
    """Result for a single product (generate output)."""

    name: str
    count: int
    sample: list[dict[str, Any]] = Field(default_factory=list)
    truncated_rows: bool = False


class ScaffoldResult(BaseModel):
    """Canonical response contract for scaffold operations."""

    ok: bool = Field(description="Whether the operation succeeded")
    stage: str = Field(
        description="Which stage completed: render | lint | dry_run"
    )
    xml: str | None = Field(
        None,
        description="Rendered DATAMIMIC descriptor XML (None only on render error)",
    )
    error: str | None = Field(
        None,
        description="Error message if stage=render and ok=False",
    )
    summary: str | None = Field(
        None,
        description="Lint summary if stage=lint",
    )
    diagnostics: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Lint or dry-run diagnostics (verbosity controlled by response_format)",
    )
    truncated: bool = Field(
        False,
        description="Diagnostics truncated due to max_diagnostics limit",
    )
    products: list[ProductResult] = Field(
        default_factory=list,
        description="Captured sample rows per product (only when stage=dry_run)",
    )
    normalization_notes: list[str] = Field(
        default_factory=list,
        description="Notes from schema normalization (e.g. kind aliases applied)",
    )
