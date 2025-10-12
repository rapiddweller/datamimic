"""Central registry for locale-specific dataset policies.

This module centralizes overrides that historically lived inside the
`datamimic_ce.domains.locales` loader. Keeping them here avoids accidental
coupling between IO helpers and policy data while giving contributors a single
place to extend dataset behaviour.
"""

from __future__ import annotations

from collections.abc import Iterable

DEFAULT_POSTAL_CODE_FORMAT = "#####"

# Map locale identifiers to dataset codes when they do not follow the
# conventional `<language>_<COUNTRY>` pattern or need explicit overrides.
LOCALE_DATASET_OVERRIDES: dict[str, str] = {
    "en_US": "US",
    "de_DE": "DE",
    "vi_VN": "VN",
}

# Country-specific postal code formatting masks used by the address generator.
POSTAL_CODE_FORMATS: dict[str, str] = {
    "US": "#####",
    "DE": "#####",
    "VN": "######",
}

# Countries with curated condition overrides that should always be present even
# when the base dataset omits them. Values must be deterministic and ordered.
PATIENT_CONDITION_OVERRIDES: dict[str, list[str]] = {
    "DE": ["I10"],
    "US": ["I10"],
}


def get_dataset_code_override(locale: str) -> str | None:
    """Return the dataset override for the given locale, if defined."""

    normalized = locale.replace("-", "_")
    return LOCALE_DATASET_OVERRIDES.get(normalized)


def dataset_code_for_locale(locale: str) -> str:
    """Derive the dataset code for a locale, applying overrides when present."""

    normalized = locale.replace("-", "_")
    override = LOCALE_DATASET_OVERRIDES.get(normalized)
    if override:
        return override
    if "_" in normalized:
        return normalized.split("_")[-1].upper()
    return normalized.upper()


def get_postal_code_format(dataset: str) -> str:
    """Return the configured postal-code mask for the dataset."""

    return POSTAL_CODE_FORMATS.get(dataset.upper(), DEFAULT_POSTAL_CODE_FORMAT)


def get_patient_condition_overrides(dataset: str) -> list[str]:
    """Return deterministic patient condition overrides for the dataset."""

    overrides = PATIENT_CONDITION_OVERRIDES.get(dataset.upper(), [])
    # Copy to prevent callers from mutating internal state.
    return list(overrides)


def iter_locale_dataset_overrides() -> Iterable[tuple[str, str]]:
    """Yield locale → dataset override pairs (used for documentation/tests)."""

    return LOCALE_DATASET_OVERRIDES.items()
