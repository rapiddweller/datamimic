from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..determinism import canonical_json, derive_seed, hash_bytes, mix_seed, stable_uuid, with_rng
from ..exceptions import DomainError
from ..locales import SUPPORTED_DATASET_CODES, load_locale


@dataclass(frozen=True)
class PatientRequest:
    domain: str = "patient"
    version: str = "v1"
    count: int = 1
    seed: str | int = "0"
    locale: str = "en_US"
    profile_id: str | None = None
    component_id: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    clock: str = "2025-01-01T00:00:00Z"
    request_hash: str = ""


def _human_id(namespace: str, uuid_value: str) -> str:
    base = int(uuid_value.replace("-", "")[:16], 16)
    checksum = base % 97
    return f"{namespace.upper()}-{checksum:02d}"


def generate(req: PatientRequest, *, profile_seed: int | None = None) -> dict[str, Any]:
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
    person_locale = locale_pack.person
    patient_locale = locale_pack.patient

    derived_seed = derive_seed(req.seed)
    # Rule 6: use injected profile_seed when present while keeping UUID derivation stable.
    rng_root = profile_seed if profile_seed is not None else derived_seed

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

    conditions_constraint = constraints.get("conditions")
    if conditions_constraint is None:
        conditions_list = list(patient_locale["conditions"])
    else:
        conditions_list = list(conditions_constraint)
    available_conditions = set(patient_locale["conditions"])
    if not set(conditions_list).issubset(available_conditions):
        raise DomainError(
            code="invalid_constraints",
            message="constraints.conditions must be known codes",
            hint=f"Allowed values: {sorted(available_conditions)}",
            path="/constraints/conditions",
            request_hash=req.request_hash,
        )

    id_namespace = constraints.get("id_namespace", patient_locale["id_namespace"])
    insurance_pool = patient_locale["insurance_providers"]

    items: list[dict[str, Any]] = []

    for index in range(req.count):
        item_seed = mix_seed(rng_root, index)
        rng = with_rng(item_seed)
        patient_id = stable_uuid("datamimic:patient:v1", derived_seed, index)
        person_id = stable_uuid("datamimic:person:v1", derived_seed, index)
        address_id = stable_uuid("datamimic:address:v1", derived_seed, index)
        age = rng.randint(min_age, max_age)
        condition = conditions_list[index % len(conditions_list)]
        insurance = insurance_pool[index % len(insurance_pool)]

        items.append(
            {
                "id": patient_id,
                "human_id": _human_id(id_namespace, patient_id),
                "person_id": person_id,
                "address_id": address_id,
                "age": age,
                "primary_condition": condition,
                "conditions": [condition],
                "insurance_provider": insurance,
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
