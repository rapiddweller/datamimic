"""Metadata loader that links demographic profiles to group references."""

from __future__ import annotations

import csv
from functools import cache
from pathlib import Path

from ...exceptions import DomainError
from ...utils.dataset_path import dataset_path, is_strict_dataset_mode

_START = Path(__file__)


@cache
def _profile_rows(dataset: str) -> tuple[dict[str, str], ...]:
    path = dataset_path(
        "demographics",
        f"profile_meta.dmgrp_{dataset}.csv",
        start=_START,
    )
    if not path.exists():
        if is_strict_dataset_mode():
            raise FileNotFoundError(f"Missing profile metadata file profile_meta.dmgrp_{dataset}.csv")
        return tuple()
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for raw in reader:
            if not raw:
                continue
            cleaned = {key: (value.strip() if isinstance(value, str) else value) for key, value in raw.items()}
            if any(cleaned.values()):
                rows.append(cleaned)
    return tuple(rows)


def lookup_profile_row(*, dataset: str, version: str, profile_id: str, request_hash: str) -> dict[str, str] | None:
    """Return the metadata row for a dataset/version/profile combination."""

    dataset_code = dataset.upper()
    rows = _profile_rows(dataset_code)
    for row in rows:
        if (row.get("version") or "").strip() != version:
            continue
        if (row.get("profile_id") or "").strip() != profile_id:
            continue
        return row
    if is_strict_dataset_mode():
        raise DomainError(
            code="unknown_profile",
            message=(f"Profile '{profile_id}' not defined in profile_meta.dmgrp_{dataset_code}.csv"),
            hint="Add the profile metadata row or disable strict dataset mode.",
            path="/profile_id",
            request_hash=request_hash,
        )
    return None


def profile_group_refs(*, dataset: str, version: str, profile_id: str, request_hash: str) -> dict[str, str]:
    """Return group reference mapping from profile metadata (empty if unavailable)."""

    row = lookup_profile_row(dataset=dataset, version=version, profile_id=profile_id, request_hash=request_hash)
    if not row:
        return {}
    return {
        key: value
        for key, value in row.items()
        if (key.endswith("_group_ref") or key.endswith("_ref")) and (value or "").strip()
    }
