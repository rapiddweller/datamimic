"""Pure demographic sampler built on top of demographic profiles."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from random import Random
from typing import Any

from ...determinism import compute_provenance_hash
from ...utils.dataset_path import dataset_path, is_strict_dataset_mode
from .profile import (
    DemographicAgeBand,
    DemographicConditionRate,
    DemographicProfile,
    DemographicProfileId,
    SexKey,
    normalize_sex,
)

_START = Path(__file__)

GROUP_COLUMN_DIMENSIONS: Mapping[str, str] = {
    "age_group_ref": "age_band",
    "gender_group_ref": "gender_category",
    "condition_group_ref": "condition_prevalence_tier",
    "region_group_ref": "population_tier",
    "sector_group_ref": "sector_macro",
    "specialty_group_ref": "specialty_family",
    "area_cluster_ref": "area_code_cluster",
    "coverage_line_ref": "coverage_line",
}

AGE_KEY = "age_band"
CONDITION_KEY = "condition_prevalence_tier"
GENDER_KEY = "gender_category"


class MaskBoundsError(ValueError):
    """Raised when a group mask violates the configured bounds."""

    def __init__(self, dimension: str, group_id: str, key: Any, ratio: float) -> None:
        super().__init__(
            f"Mask '{group_id}' in '{dimension}' exceeds bounds for key '{key}': ratio={ratio:.3f} not in [0.5, 1.5]"
        )
        self.dimension = dimension
        self.group_id = group_id
        self.key = key
        self.ratio = ratio


def _normalize(values: dict[Any, float]) -> dict[Any, float]:
    total = sum(values.values())
    if total <= 0:
        return {}
    return {key: weight / total for key, weight in values.items() if weight > 0}


def _enforce_mask_bounds(
    base: Mapping[Any, float],
    composed: Mapping[Any, float],
    *,
    dimension: str,
    group_id: str,
) -> None:
    for key, base_weight in base.items():
        if base_weight <= 0:
            continue
        composed_weight = composed.get(key, 0.0)
        ratio = composed_weight / base_weight if base_weight else 1.0
        if ratio < 0.5 or ratio > 1.5:
            raise MaskBoundsError(dimension, group_id, key, ratio)


def _clean_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}


class GroupRegistry:
    """Cache group table rows keyed by dataset, dimension, group id, and file hash."""

    @staticmethod
    def resolve(
        dataset: str,
        version: str,
        dimension: str,
        group_id: str,
    ) -> tuple[tuple[dict[str, str], ...], str | None, str | None]:
        dataset_code = dataset.upper()
        path = dataset_path("groups", dimension, f"{dimension}_{dataset_code}.csv", start=_START)
        if not path.exists():
            if is_strict_dataset_mode():
                raise FileNotFoundError(
                    f"Missing group dataset '{dimension}_{dataset_code}.csv' under domain_data/groups"
                )
            return tuple(), None, None

        provenance_hash = compute_provenance_hash([str(path)])
        matches = GroupRegistry._resolve(
            dataset_code,
            version,
            dimension,
            group_id,
            provenance_hash,
            str(path),
        )
        return matches, str(path), provenance_hash

    @staticmethod
    @lru_cache(maxsize=128)
    def _resolve(
        dataset: str,
        version: str,
        dimension: str,
        group_id: str,
        file_hash: str,
        path_str: str,
    ) -> tuple[dict[str, str], ...]:
        del version, file_hash  # included in cache key for busting purposes
        path = Path(path_str)
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows: list[dict[str, str]] = []
            for raw in reader:
                if not raw:
                    continue
                cleaned = _clean_row(raw)
                if any(cleaned.values()):
                    rows.append(cleaned)

        return tuple(row for row in rows if (row.get("group_id") or "").strip() == group_id)


def load_group_table(
    dataset: str,
    version: str,
    group_dimension: str,
    group_id: str,
) -> tuple[dict[str, float] | dict[tuple[int, int], float], tuple[str, str] | None]:
    """Load mask weights for a group dimension, normalized to sum ≈ 1."""

    matches, path_str, file_hash = GroupRegistry.resolve(
        dataset,
        version,
        group_dimension,
        group_id,
    )

    if not matches:
        if path_str and is_strict_dataset_mode():
            raise ValueError(f"Group id '{group_id}' not found in {group_dimension}_{dataset.upper()}.csv")
        return {}, None

    dataset_code = dataset.upper()
    parsed: dict[Any, float]
    if group_dimension == AGE_KEY:
        parsed = {}
        for row in matches:
            try:
                min_age = int(row["min_age"])
                max_age = int(row["max_age"])
                weight = float(row["weight"])
            except (TypeError, ValueError, KeyError) as exc:  # pragma: no cover - schema guard
                raise ValueError(
                    f"Invalid age band row for group '{group_id}' in {group_dimension}_{dataset_code}.csv"
                ) from exc
            parsed[(min_age, max_age)] = parsed.get((min_age, max_age), 0.0) + weight
    elif group_dimension == CONDITION_KEY:
        parsed = {}
        for row in matches:
            condition = (row.get("condition") or "").strip()
            parsed[condition] = parsed.get(condition, 0.0) + float(row.get("weight", 0) or 0)
    elif group_dimension == GENDER_KEY:
        parsed = {}
        for row in matches:
            gender = normalize_sex(row.get("gender"))
            parsed[gender] = parsed.get(gender, 0.0) + float(row.get("weight", 0) or 0)
    else:
        value_column = next(
            (key for key in matches[0] if key not in {"group_id", "weight"}),
            None,
        )
        if value_column is None:
            raise ValueError(f"Group table '{group_dimension}_{dataset_code}.csv' lacks value columns")
        parsed = {}
        for row in matches:
            value_key = (row.get(value_column) or "").strip()
            parsed[value_key] = parsed.get(value_key, 0.0) + float(row.get("weight", 0) or 0)

    normalized = _normalize(parsed)
    if not normalized and parsed:
        # All weights zero: treat as uniform mask over provided keys.
        uniform_weight = 1.0 / len(parsed)
        normalized = {key: uniform_weight for key in parsed}

    provenance = None
    if normalized and path_str and file_hash:
        provenance = (path_str, file_hash)

    return normalized, provenance


def compose_weights(base: Mapping[Any, float], mask: Mapping[Any, float] | None) -> dict[Any, float]:
    """Compose base priors with a mask and normalize."""

    if not base:
        return {}
    if not mask:
        return _normalize(dict(base))

    combined: dict[Any, float] = {}
    for key, base_weight in base.items():
        if base_weight <= 0:
            continue
        mask_weight = mask.get(key)
        if mask_weight is None:
            continue
        combined[key] = base_weight * mask_weight

    if not combined:
        return _normalize(dict(base))
    normalized = _normalize(combined)
    if not normalized:
        return _normalize(dict(base))
    return normalized


@dataclass(frozen=True)
class DemographicSample:
    """Sampled demographic attributes for a single entity."""

    age: int | None
    sex: SexKey
    conditions: frozenset[str]


class DemographicSampler:
    """Pure sampler that draws ages, sexes and conditions from a profile."""

    def __init__(self, profile: DemographicProfile):
        self._profile = profile
        self._group_masks: dict[str, dict[Any, float]] = {}
        self._provenance_records: dict[str, str] = {}
        self._dimension_provenance: dict[str, str] = {}

        self._age_base_weights = self._build_age_weight_map(profile)
        self._age_effective_weights = {
            sex: compose_weights(weights, None) for sex, weights in self._age_base_weights.items()
        }

        self._condition_base_strength = self._build_condition_strength(profile)
        self._condition_total_strength = sum(self._condition_base_strength.values()) or 1.0
        self._condition_base_norm = compose_weights(self._condition_base_strength, None)
        self._condition_effective_weights = dict(self._condition_base_norm)
        self._condition_scalars = {condition: 1.0 for condition in self._condition_base_strength}

        self._sex_weight_base = self._build_sex_weight_map(profile)
        self._sex_weights = dict(self._sex_weight_base)

        self._sex_choices = self._build_sex_choices(profile)
        self._age_cdf: dict[SexKey, list[tuple[float, DemographicAgeBand]]] = {}
        self._rebuild_age_cdfs()

    @property
    def profile_id(self) -> DemographicProfileId:
        return self._profile.profile_id

    def provenance_hash(self) -> str:
        if not self._provenance_records:
            return ""
        return compute_provenance_hash(sorted(self._provenance_records.keys()))

    def provenance_descriptor(self) -> dict[str, str]:
        return dict(self._provenance_records)

    def group_mask(self, dimension: str) -> dict[Any, float]:
        """Expose the resolved mask for a given group dimension."""

        return dict(self._group_masks.get(dimension, {}))

    def age_band_weights(self, sex: SexKey) -> dict[tuple[int, int], float]:
        """Return the effective age band weights for a sex bucket."""

        return dict(self._age_effective_weights.get(sex, {}))

    def condition_weights(self) -> dict[str, float]:
        """Return the effective normalized condition distribution."""

        return dict(self._condition_effective_weights)

    def sex_weights(self) -> dict[SexKey, float]:
        """Return the effective weights for each sex option."""

        return dict(self._sex_weights)

    def apply_profile_groups(
        self,
        profile_row: Mapping[str, Any],
        dataset: str,
        version: str,
    ) -> DemographicSampler:
        """Hydrate sampler masks from profile metadata and group tables."""

        for column, dimension in GROUP_COLUMN_DIMENSIONS.items():
            value = (profile_row.get(column) or "").strip()
            if not value:
                continue
            mask, provenance = load_group_table(dataset, version, dimension, value)
            if dimension == AGE_KEY:
                self._apply_age_mask(mask, dimension=dimension, group_id=value, provenance=provenance)
            elif dimension == CONDITION_KEY:
                self._apply_condition_mask(
                    mask,
                    dimension=dimension,
                    group_id=value,
                    provenance=provenance,
                )
            elif dimension == GENDER_KEY:
                self._apply_gender_mask(
                    mask,
                    dimension=dimension,
                    group_id=value,
                    provenance=provenance,
                )
            else:
                if mask:
                    self._group_masks[dimension] = mask
                    self._register_provenance(dimension, provenance)
                else:
                    self._group_masks.pop(dimension, None)
                    self._clear_provenance(dimension)
        return self

    def sample_age_sex(self, rng: Random) -> tuple[int, SexKey]:
        """Sample an age band and sex using cumulative weights."""

        sex = self._choose_sex(rng)
        bands = self._age_cdf.get(sex) or self._age_cdf.get(None)
        if not bands:
            raise ValueError("No age bands available for demographic sampling")
        pick = rng.random()
        for threshold, band in bands:
            if pick <= threshold:
                age = rng.randint(band.age_min, band.age_max)
                return age, sex
        # Numerical precision might leave pick slightly above the last threshold.
        last_band = bands[-1][1]
        # Guarantee a return even when float rounding pushes us past the final threshold.
        return rng.randint(last_band.age_min, last_band.age_max), sex

    def sample_conditions(self, age: int, sex: SexKey, rng: Random) -> frozenset[str]:
        """Sample independent conditions based on prevalence tables."""

        selected: set[str] = set()
        normalized_sex = normalize_sex(sex)
        for condition, rates in self._profile.condition_rates.items():
            rate = self._select_rate(rates, age, normalized_sex)
            if rate is None:
                continue
            multiplier = self._condition_scalars.get(condition, 1.0)
            effective_prevalence = min(1.0, max(0.0, rate.prevalence * multiplier))
            if effective_prevalence <= 0.0:
                continue
            if rng.random() <= effective_prevalence:
                selected.add(condition)
        return frozenset(selected)

    def _select_rate(
        self,
        rates: Iterable[DemographicConditionRate],
        age: int,
        sex: SexKey,
    ) -> DemographicConditionRate | None:
        # Prefer exact sex match, otherwise fall back to combined entries.
        exact_match = None
        fallback = None
        for rate in rates:
            if not rate.matches(age=age, sex=sex):
                continue
            if rate.sex is None:
                fallback = rate
            else:
                exact_match = rate
                break
        return exact_match or fallback

    def _rebuild_age_cdfs(self) -> None:
        cdfs: dict[SexKey, list[tuple[float, DemographicAgeBand]]] = {}
        for sex, bands in self._profile.age_bands.items():
            weights = self._age_effective_weights.get(sex)
            if not weights:
                weights = compose_weights(self._age_base_weights.get(sex, {}), None)
            cumulative = 0.0
            cdf: list[tuple[float, DemographicAgeBand]] = []
            for band in bands:
                key = (band.age_min, band.age_max)
                weight = weights.get(key, 0.0)
                if weight <= 0:
                    continue
                cumulative += weight
                cdf.append((cumulative, band))
            if not cdf:
                continue
            final_threshold, _ = cdf[-1]
            if abs(final_threshold - 1.0) > 1e-9:
                adjust = final_threshold
                cdf = [(threshold / adjust, band) for threshold, band in cdf]
            cdfs[sex] = cdf
        self._age_cdf = cdfs

    def _build_sex_choices(self, profile: DemographicProfile) -> tuple[SexKey, ...]:
        # Use deterministic ordering so seeded RNGs replay the same sex sequence across runs.
        sexes = sorted(sex for sex in profile.sexes() if sex is not None)
        if not sexes:
            return (None,)
        return tuple(sexes)

    def _choose_sex(self, rng: Random) -> SexKey:
        if not self._sex_choices:
            return None
        weights = [self._sex_weights.get(sex, 0.0) for sex in self._sex_choices]
        total = sum(weights)
        if total <= 0:
            return self._sex_choices[0]
        pick = rng.random() * total
        cumulative = 0.0
        for sex, weight in zip(self._sex_choices, weights, strict=False):
            cumulative += weight
            if pick <= cumulative:
                return sex
        return self._sex_choices[-1]

    def _apply_age_mask(
        self,
        mask: Mapping[Any, float],
        *,
        dimension: str,
        group_id: str,
        provenance: tuple[str, str] | None,
    ) -> None:
        if not mask:
            self._group_masks.pop(AGE_KEY, None)
            self._clear_provenance(AGE_KEY)
            self._rebuild_age_cdfs()
            return

        proposed: dict[SexKey, dict[tuple[int, int], float]] = {}
        violation: MaskBoundsError | None = None
        for sex, base_weights in self._age_base_weights.items():
            composed = compose_weights(base_weights, mask)
            try:
                _enforce_mask_bounds(base_weights, composed, dimension=dimension, group_id=group_id)
            except MaskBoundsError as exc:  # pragma: no cover - exercised in strict mode tests
                violation = exc
                break
            proposed[sex] = composed

        if violation:
            if is_strict_dataset_mode():
                raise violation
            # Non-strict mode: revert to baseline weights without applying the mask.
            self._age_effective_weights = {
                sex: compose_weights(weights, None) for sex, weights in self._age_base_weights.items()
            }
            self._group_masks.pop(AGE_KEY, None)
            self._clear_provenance(AGE_KEY)
            self._rebuild_age_cdfs()
            return

        self._age_effective_weights.update(proposed)
        self._group_masks[AGE_KEY] = dict(mask)
        self._register_provenance(AGE_KEY, provenance)
        self._rebuild_age_cdfs()

    def _apply_condition_mask(
        self,
        mask: Mapping[Any, float],
        *,
        dimension: str,
        group_id: str,
        provenance: tuple[str, str] | None,
    ) -> None:
        if not self._condition_base_norm:
            return

        effective_norm = compose_weights(self._condition_base_norm, mask if mask else None)
        if not effective_norm:
            effective_norm = dict(self._condition_base_norm)

        try:
            _enforce_mask_bounds(
                self._condition_base_norm,
                effective_norm,
                dimension=dimension,
                group_id=group_id,
            )
        except MaskBoundsError as exc:
            if is_strict_dataset_mode():
                raise exc
            effective_norm = dict(self._condition_base_norm)
            self._group_masks.pop(CONDITION_KEY, None)
            self._clear_provenance(CONDITION_KEY)
            self._condition_effective_weights = effective_norm
            self._condition_scalars = {condition: 1.0 for condition in self._condition_base_strength}
            return

        total = self._condition_total_strength
        scalars: dict[str, float] = {}
        for condition, base_strength in self._condition_base_strength.items():
            effective_strength = effective_norm.get(condition, 0.0) * total
            if base_strength > 0:
                scalars[condition] = effective_strength / base_strength
            else:
                scalars[condition] = 0.0

        self._condition_effective_weights = effective_norm
        self._condition_scalars = scalars
        if mask:
            self._group_masks[CONDITION_KEY] = dict(mask)
            self._register_provenance(CONDITION_KEY, provenance)
        else:
            self._group_masks.pop(CONDITION_KEY, None)
            self._clear_provenance(CONDITION_KEY)

    def _apply_gender_mask(
        self,
        mask: Mapping[Any, float],
        *,
        dimension: str,
        group_id: str,
        provenance: tuple[str, str] | None,
    ) -> None:
        composed = compose_weights(self._sex_weight_base, mask if mask else None)
        if not composed:
            composed = dict(self._sex_weight_base)

        try:
            _enforce_mask_bounds(
                self._sex_weight_base,
                composed,
                dimension=dimension,
                group_id=group_id,
            )
        except MaskBoundsError as exc:
            if is_strict_dataset_mode():
                raise exc
            composed = dict(self._sex_weight_base)
            self._group_masks.pop(GENDER_KEY, None)
            self._sex_weights = composed
            self._clear_provenance(GENDER_KEY)
            return

        self._sex_weights = composed
        if mask:
            self._group_masks[GENDER_KEY] = dict(mask)
            self._register_provenance(GENDER_KEY, provenance)
        else:
            self._group_masks.pop(GENDER_KEY, None)
            self._clear_provenance(GENDER_KEY)

    def _register_provenance(self, dimension: str, provenance: tuple[str, str] | None) -> None:
        if not provenance:
            self._clear_provenance(dimension)
            return
        path, file_hash = provenance
        if not path or not file_hash:
            self._clear_provenance(dimension)
            return
        normalized = Path(path).resolve().as_posix()
        self._dimension_provenance[dimension] = normalized
        self._provenance_records[normalized] = file_hash

    def _clear_provenance(self, dimension: str) -> None:
        path = self._dimension_provenance.pop(dimension, None)
        if not path:
            return
        if path not in self._dimension_provenance.values():
            self._provenance_records.pop(path, None)

    def _build_age_weight_map(self, profile: DemographicProfile) -> dict[SexKey, dict[tuple[int, int], float]]:
        weights: dict[SexKey, dict[tuple[int, int], float]] = {}
        for sex, bands in profile.age_bands.items():
            weights[sex] = {(band.age_min, band.age_max): band.weight for band in bands}
        return weights

    def _build_condition_strength(self, profile: DemographicProfile) -> dict[str, float]:
        strengths: dict[str, float] = {}
        for condition, rates in profile.condition_rates.items():
            if not rates:
                continue
            total = sum(rate.prevalence for rate in rates)
            strengths[condition] = total / len(rates)
        return strengths

    def _build_sex_weight_map(self, profile: DemographicProfile) -> dict[SexKey, float]:
        sexes = [sex for sex in profile.sexes() if sex is not None]
        if not sexes:
            return {None: 1.0}
        weight = 1.0 / len(sexes)
        return {sex: weight for sex in sexes}
