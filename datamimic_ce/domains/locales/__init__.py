from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from datamimic_ce.utils.file_util import FileUtil

from ..common.locale_registry import (
    dataset_code_for_locale,
    get_patient_condition_overrides,
    get_postal_code_format,
)
from ..common.profile_components import SUPPORTED_COMPONENT_DATASETS
from ..utils.dataset_path import dataset_path, is_strict_dataset_mode
from ..utils.supported_datasets import compute_supported_datasets


@dataclass(frozen=True)
class LocalePack:
    person: dict[str, Any]
    address: dict[str, Any]
    doctor: dict[str, Any]
    patient: dict[str, Any]


_START = Path(__file__)

_PERSON_DATASETS = compute_supported_datasets(
    [
        "common/person/givenName_male_{CC}.csv",
        "common/person/givenName_female_{CC}.csv",
        "common/person/familyName_{CC}.csv",
    ],
    start=_START,
)
_ADDRESS_DATASETS = compute_supported_datasets(
    [
        "common/street/street_{CC}.csv",
        "common/city/city_{CC}.csv",
        "common/state/state_{CC}.csv",
    ],
    start=_START,
)
_DOCTOR_DATASETS = compute_supported_datasets(
    [
        "healthcare/medical/specialties_{CC}.csv",
        "healthcare/medical/hospitals_{CC}.csv",
        "common/person/title_{CC}.csv",
    ],
    start=_START,
)
_PATIENT_DATASETS = compute_supported_datasets(
    [
        "healthcare/medical/medical_conditions_{CC}.csv",
        "healthcare/medical/insurance_providers_{CC}.csv",
    ],
    start=_START,
)

_SUPPORTED_DATASETS = (
    _PERSON_DATASETS & _ADDRESS_DATASETS & _DOCTOR_DATASETS & _PATIENT_DATASETS & SUPPORTED_COMPONENT_DATASETS
)

SUPPORTED_DATASETS: frozenset[str] = frozenset(_SUPPORTED_DATASETS)
SUPPORTED_DATASET_CODES: tuple[str, ...] = tuple(sorted(SUPPORTED_DATASETS))


def _dataset_for_locale(locale: str) -> str:
    return dataset_code_for_locale(locale)


def _ensure_supported_dataset(locale: str, dataset: str) -> None:
    if dataset not in SUPPORTED_DATASETS:
        supported_hint = ", ".join(SUPPORTED_DATASET_CODES) if SUPPORTED_DATASETS else "<none>"
        raise ValueError(
            f"Locale '{locale}' maps to dataset '{dataset}' which lacks the required domain datasets. "
            f"Supported dataset codes: {supported_hint}"
        )


def _clean(value: str) -> str:
    return value.strip().strip('"').replace("\ufeff", "")


def _detect_delimiter(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as handle:
            sample = handle.readline()
    except FileNotFoundError:
        return ","
    if sample.count(";") >= sample.count(",") and ";" in sample:
        return ";"
    return ","


def _read_rows(path: Path, *, delimiter: str | None = None) -> list[list[str]]:
    delim = delimiter or _detect_delimiter(path)
    rows: list[list[str]] = []
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle, delimiter=delim)
            for row in reader:
                cleaned = [_clean(cell) for cell in row if cell is not None]
                if any(cell for cell in cleaned):
                    rows.append(cleaned)
    except FileNotFoundError:
        if is_strict_dataset_mode():
            raise
        return []
    return rows


def _read_column_values(path: Path, *, column_index: int, column_name: str | None = None) -> list[str]:
    rows = _read_rows(path)
    if not rows:
        return []
    if column_name is not None and len(rows[0]) > column_index:
        header_value = rows[0][column_index].lower()
        if header_value == column_name.lower():
            rows = rows[1:]
    return [row[column_index] for row in rows if len(row) > column_index and row[column_index]]


def _read_weighted_values(path: Path) -> list[str]:
    try:
        values, _ = FileUtil.read_wgt_file(path)
    except FileNotFoundError:
        if is_strict_dataset_mode():
            raise
        return []
    return [_clean(value) for value in values if _clean(value)]


def _read_dict_column(path: Path, column: str) -> list[str]:
    delim = _detect_delimiter(path)
    try:
        records = FileUtil.read_csv_to_dict_list(path, delim)
    except FileNotFoundError:
        if is_strict_dataset_mode():
            raise
        return []
    cleaned: list[str] = []
    for record in records:
        value = record.get(column)
        if value is None:
            continue
        cleaned_value = _clean(str(value))
        if cleaned_value:
            cleaned.append(cleaned_value)
    return cleaned


def _unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _ensure_values(values: Sequence[str], dataset: str, description: str) -> None:
    if values:
        return
    raise ValueError(f"Dataset '{dataset}' is missing required {description} in domain_data.")


def _country_name(dataset: str) -> str:
    path = dataset_path("common", f"country_{dataset}.csv", start=_START)
    rows = _read_rows(path)
    code = dataset.upper()
    for row in rows:
        if row and row[0].upper() == code and len(row) >= 5:
            return row[4]
    return code


def _load_person_locale(dataset: str) -> dict[str, Any]:
    male_path = dataset_path("common", "person", f"givenName_male_{dataset}.csv", start=_START)
    female_path = dataset_path("common", "person", f"givenName_female_{dataset}.csv", start=_START)
    family_path = dataset_path("common", "person", f"familyName_{dataset}.csv", start=_START)

    male_names = _read_weighted_values(male_path)
    female_names = _read_weighted_values(female_path)
    family_names = _read_weighted_values(family_path)

    _ensure_values(male_names, dataset, "male given names")
    _ensure_values(female_names, dataset, "female given names")
    _ensure_values(family_names, dataset, "family names")

    first_names = {
        "M": list(male_names),
        "F": list(female_names),
        "X": _unique(list(male_names) + list(female_names)),
    }

    nationality = _country_name(dataset)

    return {
        "sexes": ["F", "M", "X"],
        "first_names": first_names,
        "last_names": list(family_names),
        "nationalities": [nationality],
        "default_age_range": {"min": 18, "max": 85},
    }


def _load_address_locale(dataset: str) -> dict[str, Any]:
    street_path = dataset_path("common", "street", f"street_{dataset}.csv", start=_START)
    city_path = dataset_path("common", "city", f"city_{dataset}.csv", start=_START)
    state_path = dataset_path("common", "state", f"state_{dataset}.csv", start=_START)

    streets = _read_weighted_values(street_path)
    cities = _read_column_values(city_path, column_index=1, column_name="name")
    states = _read_column_values(state_path, column_index=1, column_name="name")

    _ensure_values(streets, dataset, "street names")
    _ensure_values(cities, dataset, "cities")
    _ensure_values(states, dataset, "states")

    postal_format = get_postal_code_format(dataset)

    return {
        "street_names": list(streets),
        "cities": list(cities),
        "states": list(states),
        "postal_code_format": postal_format,
        "country_code": dataset,
    }


def _load_doctor_locale(dataset: str) -> dict[str, Any]:
    specialties_path = dataset_path("healthcare", "medical", f"specialties_{dataset}.csv", start=_START)
    hospitals_path = dataset_path("healthcare", "medical", f"hospitals_{dataset}.csv", start=_START)
    titles_path = dataset_path("common", "person", f"title_{dataset}.csv", start=_START)

    specialties = _read_dict_column(specialties_path, "specialty")
    hospitals = _read_weighted_values(hospitals_path)
    titles = _read_weighted_values(titles_path)

    _ensure_values(specialties, dataset, "doctor specialties")
    _ensure_values(hospitals, dataset, "hospital names")
    _ensure_values(titles, dataset, "doctor titles")

    license_prefix = f"{dataset}-MED"

    return {
        "specialties": list(specialties),
        "license_prefix": license_prefix,
        "titles": list(titles),
        "hospitals": list(hospitals),
    }


def _load_patient_locale(dataset: str) -> dict[str, Any]:
    conditions_path = dataset_path("healthcare", "medical", f"medical_conditions_{dataset}.csv", start=_START)
    insurance_path = dataset_path("healthcare", "medical", f"insurance_providers_{dataset}.csv", start=_START)

    conditions = _read_dict_column(conditions_path, "condition")
    overrides = get_patient_condition_overrides(dataset)
    combined_conditions = _unique(overrides + conditions)

    _ensure_values(combined_conditions, dataset, "patient conditions")

    insurance = _read_weighted_values(insurance_path)
    _ensure_values(insurance, dataset, "insurance providers")

    id_namespace = f"patient-{dataset.lower()}"

    return {
        "conditions": list(combined_conditions),
        "id_namespace": id_namespace,
        "insurance_providers": list(insurance),
    }


@cache
def load_locale(locale: str, version: str) -> LocalePack:
    if version != "v1":
        raise ValueError(f"Unsupported locale version: {version}")
    dataset = _dataset_for_locale(locale)
    _ensure_supported_dataset(locale, dataset)
    try:
        person = _load_person_locale(dataset)
        address = _load_address_locale(dataset)
        doctor = _load_doctor_locale(dataset)
        patient = _load_patient_locale(dataset)
    except FileNotFoundError as exc:
        raise ValueError(f"Dataset '{dataset}' is missing required files: {exc}") from exc
    return LocalePack(person=person, address=address, doctor=doctor, patient=patient)
