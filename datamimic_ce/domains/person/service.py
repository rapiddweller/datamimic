from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..determinism import (
    canonical_json,
    derive_seed,
    frozen_clock,
    hash_bytes,
    mix_seed,
    stable_uuid,
    with_rng,
)
from ..exceptions import DomainError
from ..locales import SUPPORTED_DATASET_CODES, load_locale


@dataclass(frozen=True)
class PersonRequest:
    domain: str = "person"
    version: str = "v1"
    count: int = 1
    seed: str | int = "0"
    locale: str = "en_US"
    profile_id: str | None = None
    component_id: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    clock: str = "2025-01-01T00:00:00Z"
    request_hash: str = ""


def generate(req: PersonRequest, *, profile_seed: int | None = None) -> dict[str, Any]:
    if req.count < 0:
        raise DomainError(
            code="invalid_count",
            message="Count must be non-negative",
            hint="Provide a count >= 0",
            path="/count",
            request_hash=req.request_hash,
        )

    try:
        locale_pack = load_locale(req.locale, req.version)
    except ValueError as exc:
        hint_codes = ", ".join(SUPPORTED_DATASET_CODES) or "<none>"
        raise DomainError(
            code="unsupported_locale",
            message=str(exc),
            hint=f"Choose a locale mapping to dataset codes: {hint_codes}",
            path="/locale",
            request_hash=req.request_hash,
        ) from exc
    constraints = req.constraints or {}

    derived_seed = derive_seed(req.seed)
    # Rule 6: inject profile_seed from facade without introducing side effects.
    rng_root = profile_seed if profile_seed is not None else derived_seed
    clock_dt = frozen_clock(req.clock)
    person_locale = locale_pack.person

    age_constraints = constraints.get("age", {})
    min_age = age_constraints.get("min", person_locale["default_age_range"]["min"])
    max_age = age_constraints.get("max", person_locale["default_age_range"]["max"])

    if min_age > max_age:
        raise DomainError(
            code="invalid_constraints",
            message="constraints.age.min cannot exceed constraints.age.max",
            hint="Adjust the age range to be ascending",
            path="/constraints/age",
            request_hash=req.request_hash,
        )

    sexes: list[str]
    sex_constraint = constraints.get("sex")
    if sex_constraint is None:
        sexes = list(person_locale["sexes"])
    elif isinstance(sex_constraint, str):
        sexes = [sex_constraint]
    else:
        sexes = list(sex_constraint)
    available_sexes = set(person_locale["sexes"])
    if not set(sexes).issubset(available_sexes):
        raise DomainError(
            code="invalid_constraints",
            message="constraints.sex must be within the locale-defined set",
            hint=f"Allowed values: {sorted(available_sexes)}",
            path="/constraints/sex",
            request_hash=req.request_hash,
        )

    items: list[dict[str, Any]] = []
    for index in range(req.count):
        item_seed = mix_seed(rng_root, index)
        rng = with_rng(item_seed)
        sex = sexes[index % len(sexes)]
        first_pool = person_locale["first_names"].get(sex) or person_locale["first_names"]["X"]
        last_pool = person_locale["last_names"]
        nationality_pool = person_locale["nationalities"]

        first_name = first_pool[rng.randrange(len(first_pool))]
        last_name = last_pool[rng.randrange(len(last_pool))]
        age = rng.randint(min_age, max_age)

        birth_month = rng.randint(1, 12)
        birth_day = rng.randint(1, 28)
        birth_year = clock_dt.year - age
        birth_date = datetime(birth_year, birth_month, birth_day, tzinfo=UTC)

        person_id = stable_uuid("datamimic:person:v1", derived_seed, index)

        items.append(
            {
                "id": person_id,
                "human_id": f"PER-{person_id[:8].upper()}",
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{first_name} {last_name}",
                "sex": sex,
                "age": age,
                "date_of_birth": birth_date.date().isoformat(),
                "nationality": nationality_pool[index % len(nationality_pool)],
                "locale": req.locale,
            }
        )

    items_hash = hash_bytes(canonical_json(items))

    return {
        "domain": req.domain,
        "version": req.version,
        "request_hash": req.request_hash,
        "items": items,
        "determinism_proof": {
            "algorithm": "uuid5+sha256",
            "seed_canonical": str(derived_seed),
            "content_hash": items_hash,
        },
    }
