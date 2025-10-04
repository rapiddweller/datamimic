from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

from datamimic_ce.domains.utils.dataset_path import domain_data_root


def _codes_for_pattern(pattern: str, *, start: Path | None = None) -> set[str]:
    """Return dataset codes supported by a filename pattern under domain_data.

    Example pattern: "public_sector/administration/office_types_{CC}.csv"
    """
    root = domain_data_root(start)
    parts = Path(pattern)
    folder = root.joinpath(*parts.parts[:-1])
    fname = parts.name
    # Build a regex from the filename, replacing {CC} by two uppercase letters
    rx = re.escape(fname).replace(re.escape("{CC}"), r"([A-Z]{2})") + r"\Z"
    rxp = re.compile(rx)
    codes: set[str] = set()
    if not folder.exists():
        return codes
    for item in folder.iterdir():
        if not item.is_file():
            continue
        m = rxp.match(item.name)
        if m:
            codes.add(m.group(1).upper())
    return codes


def compute_supported_datasets(patterns: Iterable[str], *, start: Path | None = None) -> set[str]:
    """Compute the intersection of dataset codes available for all given patterns.

    Each pattern is a path relative to `domain_data` that contains a `{CC}` placeholder.
    Returns set of ISO codes for which all required files exist.
    """
    it = iter(patterns)
    try:
        first = next(it)
    except StopIteration:
        return set()

    acc = _codes_for_pattern(first, start=start)
    for p in it:
        acc &= _codes_for_pattern(p, start=start)
    return acc
