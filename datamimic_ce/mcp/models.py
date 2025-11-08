"""Pydantic models backing the MCP surface."""

from __future__ import annotations

import csv
from functools import cache
from typing import Any

from pydantic import BaseModel, Field, model_validator

from datamimic_ce.domains.common.locale_registry import dataset_code_for_locale
from datamimic_ce.domains.locales import SUPPORTED_DATASET_CODES
from datamimic_ce.domains.utils.dataset_path import dataset_path

MAX_COUNT = 10_000
_DEFAULT_LOCALE = "en_US"
_DEFAULT_CLOCK = "2025-01-01T00:00:00Z"

_DATASET_LOCALE_DEFAULTS: dict[str, str] = {
    "US": "en_US",
    "DE": "de_DE",
    "VN": "vi_VN",
}


@cache
def _default_locale_for_dataset(dataset: str) -> str | None:
    """Infer the canonical locale for a dataset using packaged metadata."""

    normalized = dataset.upper()
    explicit = _DATASET_LOCALE_DEFAULTS.get(normalized)
    if explicit:
        return explicit

    try:
        path = dataset_path("common", f"country_{normalized}.csv")
    except OSError:  # pragma: no cover - defensive fall-back for env overrides
        return None

    expected_name = f"country_{normalized}.csv"
    if path.name != expected_name or not path.exists():
        return None

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            code = row[0].strip().upper()
            if code != normalized or len(row) < 2:
                continue
            locale = row[1].strip().replace("-", "_")
            if locale:
                return locale
    return None


class GenerateArgs(BaseModel):
    """Validated request arguments for the ``generate`` MCP tool."""

    domain: str = Field(..., description="Target domain identifier")
    version: str = Field("v1", description="Domain contract version")
    count: int = Field(
        1,
        ge=0,
        le=MAX_COUNT,
        description="Number of records to generate (capped at 10k)",
    )
    seed: int | str = Field(
        "0",
        description="Seed propagated to the deterministic generators",
    )
    locale: str | None = Field(
        None,
        description="Locale identifier (e.g. en_US). Defaults to dataset derived locale",
    )
    dataset: str | None = Field(
        None,
        description=("Dataset code that implies a locale (e.g. US). Mutually exclusive with custom locale overrides."),
    )
    constraints: dict[str, Any] | None = Field(
        None,
        description="Optional domain-specific constraint overrides",
    )
    profile_id: str | None = Field(
        None,
        description="Explicit profile selection (mutually exclusive with component_id)",
    )
    component_id: str | None = Field(
        None,
        description="Component-driven profile selection (mutually exclusive with profile_id)",
    )
    clock: str = Field(
        _DEFAULT_CLOCK,
        description="ISO8601 timestamp establishing the deterministic reference clock",
    )

    @model_validator(mode="after")
    def _enforce_contracts(self) -> GenerateArgs:
        if self.profile_id and self.component_id:
            raise ValueError("profile_id and component_id cannot be combined")

        resolved_dataset = self._normalize_dataset(self.dataset)
        resolved_locale = self._normalize_locale(self.locale, resolved_dataset)

        if self.locale and resolved_dataset:
            dataset_for_locale = dataset_code_for_locale(self.locale)
            if dataset_for_locale.upper() != resolved_dataset:
                raise ValueError("locale and dataset disagree on the backing data pack")

        object.__setattr__(self, "dataset", resolved_dataset)
        object.__setattr__(self, "locale", resolved_locale)
        return self

    @staticmethod
    def _normalize_dataset(raw: str | None) -> str | None:
        """Canonicalize dataset identifiers and enforce the supported list."""
        if raw is None:
            return None
        normalized = raw.strip().upper()
        if not normalized:
            return None
        if normalized not in SUPPORTED_DATASET_CODES:
            supported = ", ".join(SUPPORTED_DATASET_CODES)
            raise ValueError(
                f"Unsupported dataset '{normalized}'. Expected one of [{supported}]",
            )
        return normalized

    @staticmethod
    def _normalize_locale(locale: str | None, dataset: str | None) -> str:
        """Derive the locale, falling back to dataset defaults or the global default."""
        if locale:
            return locale
        if dataset:
            inferred = _default_locale_for_dataset(dataset)
            if inferred:
                return inferred
        return _DEFAULT_LOCALE

    def to_payload(self) -> dict[str, Any]:
        """Serialize the request into the facade payload shape."""
        payload: dict[str, Any] = {
            "domain": self.domain,
            "version": self.version,
            "count": self.count,
            "seed": self.seed,
            "locale": self.locale,
            "constraints": self.constraints or {},
            "clock": self.clock,
        }
        if self.profile_id:
            payload["profile_id"] = self.profile_id
        if self.component_id:
            payload["component_id"] = self.component_id
        return payload


__all__ = ["GenerateArgs", "MAX_COUNT"]
