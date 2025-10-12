"""Profile component resolver built on dataset_path to preserve determinism.

This module enforces repo rules around dataset placement (rules 1-3) while
providing a deterministic mapping from component identifiers to profile seeds
and constraint overrides.
"""

from __future__ import annotations

import csv
import json
from functools import cache
from pathlib import Path
from typing import Any

from ..exceptions import DomainError
from ..utils.dataset_path import dataset_path, is_strict_dataset_mode
from ..utils.supported_datasets import compute_supported_datasets
from .locale_registry import dataset_code_for_locale

_START = Path(__file__)
_COMPONENT_PATTERN = "demographics/demographic_components_{CC}.csv"
SUPPORTED_COMPONENT_DATASETS = frozenset(compute_supported_datasets([_COMPONENT_PATTERN], start=_START))


@cache
def _component_rows(dataset: str) -> tuple[dict[str, str], ...]:
    """Load component rows for a dataset via dataset_path (rules 1-3)."""

    path = dataset_path("demographics", f"demographic_components_{dataset}.csv", start=_START)
    if not path.exists():
        if is_strict_dataset_mode():
            raise FileNotFoundError(f"Missing component dataset: {path}")
        return tuple()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            cleaned = {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
            if any(cleaned.values()):
                rows.append(cleaned)
    return tuple(rows)


def resolve_component_profile(
    *,
    locale: str,
    version: str,
    component_id: str,
    request_hash: str,
) -> tuple[str, dict[str, Any]]:
    """Resolve a component to (dmgrp_profile_id, constraints) enforcing strict mode."""

    if version != "v1":
        raise DomainError(
            code="unsupported_component_version",
            message=f"Unsupported component version: {version}",
            hint="Only v1 components are currently available.",
            path="/component_id",
            request_hash=request_hash,
        )

    dataset = dataset_code_for_locale(locale)
    dataset_upper = dataset.upper()
    strict_mode = is_strict_dataset_mode()
    if dataset_upper not in SUPPORTED_COMPONENT_DATASETS:
        if strict_mode:
            raise DomainError(
                code="unsupported_component_dataset",
                message=(f"Locale '{locale}' maps to dataset '{dataset_upper}' without demographic components"),
                hint=(f"Add demographic_components_{dataset_upper}.csv under domain_data or disable strict mode"),
                path="/component_id",
                request_hash=request_hash,
            )
        return component_id, {}

    try:
        rows = _component_rows(dataset_upper)
    except FileNotFoundError as exc:
        if strict_mode:
            raise DomainError(
                code="missing_component_dataset",
                message=str(exc),
                hint=(f"Ensure demographic_components_{dataset_upper}.csv exists for locale '{locale}'"),
                path="/component_id",
                request_hash=request_hash,
            ) from exc
        return component_id, {}

    lookup = component_id.strip()
    for row in rows:
        if (row.get("component_id") or "").strip() != lookup:
            continue
        profile_col = row.get("dmgrp_profile_id") or row.get("profile_id")
        profile_id = (profile_col or lookup).strip() or lookup
        constraints_raw = (row.get("constraints_json") or "").strip()
        if constraints_raw:
            try:
                constraints = json.loads(constraints_raw)
            except json.JSONDecodeError as exc:
                raise DomainError(
                    code="invalid_component_constraints",
                    message=(f"Component '{component_id}' has invalid constraints_json payload"),
                    hint="Fix the JSON string stored in constraints_json column.",
                    path="/component_id",
                    request_hash=request_hash,
                ) from exc
        else:
            constraints = {}
        return profile_id, constraints

    if strict_mode:
        raise DomainError(
            code="unknown_component",
            message=(f"Component '{component_id}' is not defined for dataset '{dataset_upper}'"),
            hint=(f"Add a row with component_id '{component_id}' to demographic_components_{dataset_upper}.csv"),
            path="/component_id",
            request_hash=request_hash,
        )

    return component_id, {}
