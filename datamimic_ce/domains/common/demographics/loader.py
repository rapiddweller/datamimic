"""CSV loader for demographic profiles."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil

from .profile import (
    DemographicAgeBand,
    DemographicConditionRate,
    DemographicProfile,
    DemographicProfileId,
    SexKey,
    normalize_sex,
)

_REQUIRED_FILES = {
    "age_pyramid.dmgrp.csv",
    "condition_rates.dmgrp.csv",
}


class DemographicProfileError(ValueError):
    """Raised when demographic CSV files are invalid."""


def load_demographic_profile(directory: Path, dataset: str, version: str) -> DemographicProfile:
    """Load a demographic profile from the given directory."""

    base_dir = Path(directory)
    if not base_dir.exists():
        raise DemographicProfileError(f"Demographic directory '{base_dir}' does not exist")

    files = {path.name: path for path in base_dir.glob("*.dmgrp.csv")}
    missing = _REQUIRED_FILES.difference(files)
    if missing:
        raise DemographicProfileError(
            f"Missing demographic files {sorted(missing)} in '{base_dir}'. Ensure required CSVs exist."
        )

    age_bands = _load_age_bands(files["age_pyramid.dmgrp.csv"], dataset, version)
    condition_rates = _load_condition_rates(files["condition_rates.dmgrp.csv"], dataset, version)

    profile = DemographicProfile(
        profile_id=DemographicProfileId(dataset=dataset, version=version),
        age_bands=age_bands,
        condition_rates=condition_rates,
    )
    return profile


def _load_age_bands(file_path: Path, dataset: str, version: str) -> dict[SexKey, tuple[DemographicAgeBand, ...]]:
    rows = FileUtil.read_csv_to_dict_list(file_path, separator=",")
    grouped: defaultdict[SexKey, list[DemographicAgeBand]] = defaultdict(list)
    for idx, row in enumerate(rows, start=2):
        _ensure_dataset_version(row, dataset, version, file_path, idx)
        sex = normalize_sex(row.get("sex"))
        try:
            age_min = int(row["age_min"])
            age_max = int(row["age_max"])
            weight = float(row["weight"])
        except (TypeError, ValueError) as exc:
            raise DemographicProfileError(
                f"Invalid numeric value in '{file_path}' line {idx}: {exc}."
                " Expected integers for age_min/age_max and float for weight."
            ) from exc
        if age_min > age_max:
            raise DemographicProfileError(
                f"age_min must be <= age_max in '{file_path}' line {idx}: got {age_min}>{age_max}."
            )
        if weight < 0:
            raise DemographicProfileError(f"weight must be non-negative in '{file_path}' line {idx}: got {weight}.")
        grouped[sex].append(
            DemographicAgeBand(
                sex=sex,
                age_min=age_min,
                age_max=age_max,
                weight=weight,
            )
        )

    normalized: dict[SexKey, tuple[DemographicAgeBand, ...]] = {}
    for sex, bands in grouped.items():
        sorted_bands = sorted(bands, key=lambda b: (b.age_min, b.age_max))
        _validate_band_coverage(sorted_bands, file_path, sex)
        total_weight = sum(b.weight for b in sorted_bands)
        if not _is_close(total_weight, 1.0):
            raise DemographicProfileError(
                f"Weights must sum to 1.0 per sex in '{file_path}' for sex='{sex or ''}' (sum={total_weight:.6f})."
            )
        normalized[sex] = tuple(sorted_bands)
    if not normalized:
        raise DemographicProfileError(f"No rows parsed from '{file_path}'.")
    return normalized


def _load_condition_rates(
    file_path: Path, dataset: str, version: str
) -> dict[str, tuple[DemographicConditionRate, ...]]:
    rows = FileUtil.read_csv_to_dict_list(file_path, separator=",")
    grouped: defaultdict[str, list[DemographicConditionRate]] = defaultdict(list)
    for idx, row in enumerate(rows, start=2):
        _ensure_dataset_version(row, dataset, version, file_path, idx)
        condition = (row.get("condition") or "").strip()
        if not condition:
            raise DemographicProfileError(
                f"Condition name missing in '{file_path}' line {idx}. Provide canonical condition labels."
            )
        sex = normalize_sex(row.get("sex"))
        try:
            age_min = int(row["age_min"])
            age_max = int(row["age_max"])
            prevalence = float(row["prevalence"])
        except (TypeError, ValueError) as exc:
            raise DemographicProfileError(
                f"Invalid numeric value in '{file_path}' line {idx}: {exc}."
                " Expected integers for age_min/age_max and float for prevalence."
            ) from exc
        if age_min > age_max:
            raise DemographicProfileError(
                f"age_min must be <= age_max in '{file_path}' line {idx}: got {age_min}>{age_max}."
            )
        if not 0.0 <= prevalence <= 1.0:
            raise DemographicProfileError(
                f"prevalence must be within [0,1] in '{file_path}' line {idx}: got {prevalence}."
            )
        grouped[condition].append(
            DemographicConditionRate(
                condition=condition,
                sex=sex,
                age_min=age_min,
                age_max=age_max,
                prevalence=prevalence,
            )
        )

    normalized: dict[str, tuple[DemographicConditionRate, ...]] = {}
    for condition, rates in grouped.items():
        normalized[condition] = tuple(sorted(rates, key=_condition_sort_key))
    return normalized


def _condition_sort_key(rate: DemographicConditionRate) -> tuple[int, int, int]:
    # Stable ordering ensures deterministic sampling and makes tests reproducible.
    return (0 if rate.sex is not None else 1, rate.age_min, rate.age_max)


def _ensure_dataset_version(
    row: dict,
    dataset: str,
    version: str,
    file_path: Path,
    line_number: int,
) -> None:
    if (row.get("dataset") or "").strip() != dataset:
        raise DemographicProfileError(f"Dataset mismatch in '{file_path}' line {line_number}: expected '{dataset}'.")
    if (row.get("version") or "").strip() != version:
        raise DemographicProfileError(f"Version mismatch in '{file_path}' line {line_number}: expected '{version}'.")


def _validate_band_coverage(bands: Iterable[DemographicAgeBand], file_path: Path, sex: SexKey) -> None:
    sorted_bands = list(bands)
    previous = None
    for band in sorted_bands:
        if previous and band.age_min <= previous.age_max:
            raise DemographicProfileError(
                f"Overlapping age bands for sex='{sex or ''}' in '{file_path}':"
                f" [{previous.age_min},{previous.age_max}] overlaps [{band.age_min},{band.age_max}]."
            )
        if previous and band.age_min > previous.age_max + 1:
            logger.warning(
                "Gap detected between age bands for sex='%s' in '%s': [%s,%s] -> [%s,%s]",
                sex or "",
                file_path,
                previous.age_min,
                previous.age_max,
                band.age_min,
                band.age_max,
            )
        previous = band
    if sorted_bands:
        if sorted_bands[0].age_min > 0:
            logger.warning(
                "Age coverage for sex='%s' in '%s' starts at %s (>0).", sex or "", file_path, sorted_bands[0].age_min
            )
        if sorted_bands[-1].age_max < 100:
            logger.warning(
                "Age coverage for sex='%s' in '%s' ends at %s (<100).", sex or "", file_path, sorted_bands[-1].age_max
            )


def _is_close(value: float, target: float, *, tolerance: float = 1e-6) -> bool:
    return abs(value - target) <= tolerance
