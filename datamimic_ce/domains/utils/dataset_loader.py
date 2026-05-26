from __future__ import annotations

import random
from collections.abc import Sequence
from pathlib import Path

from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil

"""
Lightweight helpers to load weighted datasets and pick values consistently.

WHY: Many generators do the same: load a (value, weight) CSV and perform a
weighted pick, sometimes sampling multiple without replacement. Centralize
the tiny bits to keep domain generators clean and consistent.
"""


def pick_one_weighted(rng: random.Random, values: Sequence[str], weights: Sequence[float]) -> str:
    return rng.choices(values, weights=weights, k=1)[0]


def pick_one_weighted_no_repeat(
    rng: random.Random,
    values: Sequence[str],
    weights: Sequence[float],
    *,
    last: str | None,
) -> str:
    """Pick one value by weight, excluding *last* when ≥2 distinct values exist.

    Guarantees non-repetition by filter-and-renormalise (not retry).
    Falls back to the full pool when *last* is None, not present in *values*,
    or only one distinct value exists.
    """
    if last is not None and len(set(values)) > 1:
        pool = [(v, w) for v, w in zip(values, weights, strict=True) if v != last]
        if pool:
            p_vals, p_wgts = zip(*pool, strict=True)
            return rng.choices(list(p_vals), weights=list(p_wgts), k=1)[0]
    return rng.choices(list(values), weights=list(weights), k=1)[0]


def pick_weighted_from_headered_csv(
    rng: random.Random, file_path: Path, *, value_col: str, weight_col: str = "weight"
) -> str:
    """Pick one value (by weight) from a headered CSV's named value column.

    For CSVs that carry a header row and more than the bare ``value,weight`` shape
    that :func:`load_weighted_values` expects. Raises if a required column is absent.
    """
    header, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")
    w_idx = header.get(weight_col)
    v_idx = header.get(value_col)
    if w_idx is None or v_idx is None:
        raise ValueError(
            f"{file_path} is missing required column(s): "
            f"value_col={value_col!r}, weight_col={weight_col!r} (header columns: {sorted(header)})"
        )
    choice = rng.choices(rows, weights=[float(r[w_idx]) for r in rows], k=1)[0]
    return choice[v_idx]


def sample_weighted_no_replacement(
    rng: random.Random, values: Sequence[str], weights: Sequence[float], k: int
) -> list[str]:
    pool = list(values)
    pool_w = list(weights)
    picks: list[str] = []
    for _ in range(min(k, len(pool))):
        chosen = rng.choices(pool, weights=pool_w, k=1)[0]
        picks.append(chosen)
        # remove chosen
        idx = pool.index(chosen)
        del pool[idx]
        del pool_w[idx]
    return picks


def load_weighted_values_try_dataset(
    *relative: str | Path, dataset: str | None, start: Path
) -> tuple[Sequence[str], Sequence[float]]:
    """Load weighted values from a dataset-suffixed CSV.

    Example: ("healthcare", "hospital", "name_patterns.csv", dataset="US")
    resolves "name_patterns_US.csv".
    """
    parts = [str(p) for p in relative]
    if not parts:
        raise ValueError("relative path must include a filename")

    filename = parts[-1]
    base_parts = parts[:-1]
    base_path = dataset_path(*base_parts, filename, start=start)

    # No dataset provided: treat as global file and load directly
    if not dataset:
        return FileUtil.read_wgt_file(base_path)

    # Always resolve through dataset_path() so we get consistent behavior:
    # - strict mode: no fallback, missing file will surface at read time
    # - non-strict: attempt _US fallback with a single warning per dataset
    normalized = dataset.upper()
    stem = Path(filename).stem
    suffix = Path(filename).suffix or ""
    suffixed = f"{stem}_{normalized}{suffix}"
    ds_path = dataset_path(*base_parts, suffixed, start=start)
    return FileUtil.read_wgt_file(ds_path)
