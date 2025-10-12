from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..determinism import canonical_json, derive_seed, hash_bytes, mix_seed, stable_uuid, with_rng
from ..exceptions import DomainError
from ..locales import SUPPORTED_DATASET_CODES, load_locale


@dataclass(frozen=True)
class DoctorRequest:
    domain: str = "doctor"
    version: str = "v1"
    count: int = 1
    seed: str | int = "0"
    locale: str = "en_US"
    constraints: dict[str, Any] = field(default_factory=dict)
    clock: str = "2025-01-01T00:00:00Z"
    request_hash: str = ""


def generate(req: DoctorRequest) -> dict[str, Any]:
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
    person_locale = locale_pack.person
    doctor_locale = locale_pack.doctor
    constraints = req.constraints or {}

    specialties = constraints.get("specialty")
    if specialties is None:
        requested_specialties = list(doctor_locale["specialties"])
    elif isinstance(specialties, str):
        requested_specialties = [specialties]
    else:
        requested_specialties = list(specialties)

    canonical_specialties = doctor_locale["specialties"]
    specialty_lookup = {value.casefold(): value for value in canonical_specialties}

    normalized_specialties: list[str] = []
    unknown: list[str] = []
    for requested in requested_specialties:
        key = str(requested).casefold()
        match = specialty_lookup.get(key)
        if match is None:
            unknown.append(str(requested))
        else:
            normalized_specialties.append(match)

    if unknown:
        raise DomainError(
            code="invalid_constraints",
            message="constraints.specialty must be a known specialty",
            hint=f"Allowed values: {sorted(canonical_specialties)}",
            path="/constraints/specialty",
            request_hash=req.request_hash,
        )

    if not normalized_specialties:
        normalized_specialties = list(canonical_specialties)

    license_prefix = constraints.get("license_prefix", doctor_locale["license_prefix"])

    derived_seed = derive_seed(req.seed)
    items: list[dict[str, Any]] = []

    for index in range(req.count):
        item_seed = mix_seed(derived_seed, index)
        rng = with_rng(item_seed)
        sex = person_locale["sexes"][index % len(person_locale["sexes"])]
        first_pool = person_locale["first_names"].get(sex) or person_locale["first_names"]["X"]
        first_name = first_pool[rng.randrange(len(first_pool))]
        last_name = person_locale["last_names"][rng.randrange(len(person_locale["last_names"]))]
        title = doctor_locale["titles"][rng.randrange(len(doctor_locale["titles"]))]
        specialty = normalized_specialties[index % len(normalized_specialties)]
        hospital = doctor_locale["hospitals"][index % len(doctor_locale["hospitals"])]

        doctor_id = stable_uuid("datamimic:doctor:v1", derived_seed, index)
        license_suffix = doctor_id.replace("-", "")[:8].upper()
        license_number = f"{license_prefix}-{license_suffix}"

        items.append(
            {
                "id": doctor_id,
                "human_id": f"DOC-{doctor_id[:8].upper()}",
                "first_name": first_name,
                "last_name": last_name,
                "full_name": f"{title} {first_name} {last_name}",
                "title": title,
                "specialty": specialty,
                "license_number": license_number,
                "hospital": hospital,
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
