from __future__ import annotations

import random
from collections.abc import Sequence
from pathlib import Path
from typing import TypeAlias, TypeGuard

from pandas import DataFrame

from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.engine.io.dataset_api import FileContentStorage, FileUtil, JsonValue

CsvRow: TypeAlias = tuple[str, ...]
CsvRecord: TypeAlias = dict[str, str]
CsvHeader: TypeAlias = dict[str, int]
CsvRecords: TypeAlias = list[CsvRecord]
HeaderedCsv: TypeAlias = tuple[CsvHeader, list[CsvRow]]
WeightedValues: TypeAlias = tuple[list[str], list[float]]
WeightedRecords: TypeAlias = tuple[list[float], CsvRecords]
JsonObject: TypeAlias = dict[str, JsonValue]
JsonData: TypeAlias = list[JsonObject] | JsonObject


def _is_json_records(value: JsonValue) -> TypeGuard[list[JsonObject]]:
    return isinstance(value, list) and all(isinstance(row, dict) for row in value)


def _is_headered_csv(value: object) -> TypeGuard[HeaderedCsv]:
    return (
        isinstance(value, tuple)
        and len(value) == 2
        and isinstance(value[0], dict)
        and all(isinstance(key, str) and isinstance(index, int) for key, index in value[0].items())
        and isinstance(value[1], list)
        and all(isinstance(row, tuple) and all(isinstance(cell, str) for cell in row) for row in value[1])
    )

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


def read_csv_records(file_path: Path, separator: str = ",") -> CsvRecords:
    return FileUtil.read_csv_to_dict_list(file_path, separator)


def read_headered_csv(file_path: Path, delimiter: str = ",") -> HeaderedCsv:
    header, rows = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter)
    return header, rows


def read_csv_rows(file_path: Path, delimiter: str = ",") -> list[CsvRow]:
    return FileUtil.read_csv_to_list_of_tuples_without_header(file_path, delimiter)


def read_weighted_values(file_path: Path, delimiter: str = ",") -> WeightedValues:
    return FileUtil.read_wgt_file(file_path, delimiter)


def read_multi_column_weighted_values(
    file_path: Path, weight_col_index: int = 1, delimiter: str = ","
) -> tuple[list[CsvRow], list[float]]:
    return FileUtil.read_mutil_column_wgt_file(file_path, weight_col_index, delimiter)


def read_weighted_records(file_path: Path, weight_column: str, delimiter: str = ",") -> WeightedRecords:
    weights, records = FileUtil.read_csv_having_weight_column(file_path, weight_column, delimiter)
    return weights, records


def read_weighted_dataframe(file_path: Path, separator: str = ",") -> DataFrame:
    return FileUtil.read_weight_csv(file_path, separator)


def read_json_data(file_path: Path) -> JsonData:
    value = FileUtil.read_json(file_path)
    if isinstance(value, dict):
        return value
    if _is_json_records(value):
        return value
    raise ValueError(f"JSON dataset '{file_path}' must contain an object or a list of objects")


def read_cached_headered_csv(file_path: Path, cache_key: str) -> HeaderedCsv:
    cached = FileContentStorage.load_file_with_custom_func(
        cache_key,
        lambda: FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=","),
    )
    if _is_headered_csv(cached):
        return cached
    raise ValueError(f"Cached headered CSV at '{file_path}' has an invalid shape")
