from __future__ import annotations

import json
from dataclasses import fields
from typing import Any

from .address.service import AddressRequest
from .address.service import generate as generate_address
from .common.profile_components import resolve_component_profile
from .determinism import canonical_json, derive_profile_seed, hash_bytes
from .doctor.service import DoctorRequest
from .doctor.service import generate as generate_doctor
from .exceptions import DomainError
from .patient.service import PatientRequest
from .patient.service import generate as generate_patient
from .person.service import PersonRequest
from .person.service import generate as generate_person
from .schema_registry import validate_payload

GeneratorEntry = tuple[Any, Any]


REGISTRY: dict[tuple[str, str], GeneratorEntry] = {
    ("person", "v1"): (PersonRequest, generate_person),
    ("address", "v1"): (AddressRequest, generate_address),
    ("patient", "v1"): (PatientRequest, generate_patient),
    ("doctor", "v1"): (DoctorRequest, generate_doctor),
}

# Rule 5: facade orchestrates profile/component resolution to keep services pure.
PROFILE_SEED_ENABLED: tuple[tuple[str, str], ...] = (
    ("person", "v1"),
    ("patient", "v1"),
)


def generate_domain(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise DomainError(
            code="invalid_request",
            message="Payload must be a JSON object",
            hint="Send a JSON object following the domain contract",
            path="/",
            request_hash="",
        )

    canonical_request = canonical_json(payload)
    request_hash = hash_bytes(canonical_request)

    domain = payload.get("domain")
    version = payload.get("version")

    if not isinstance(domain, str):
        raise DomainError(
            code="invalid_request",
            message="Missing or invalid 'domain' field",
            hint="Provide the target domain as a string",
            path="/domain",
            request_hash=request_hash,
        )
    if not isinstance(version, str):
        raise DomainError(
            code="invalid_request",
            message="Missing or invalid 'version' field",
            hint="Provide the target version as a string",
            path="/version",
            request_hash=request_hash,
        )

    key = (domain, version)
    if key not in REGISTRY:
        raise DomainError(
            code="unsupported_domain",
            message=f"Domain '{domain}' version '{version}' is not supported",
            hint=f"Supported domains: {sorted({k[0] for k in REGISTRY})}",
            path="/domain",
            request_hash=request_hash,
        )

    request_cls, generator = REGISTRY[key]

    validate_payload(payload, domain, "request", version, request_hash)

    request_payload = dict(payload)
    profile_seed = None
    if key in PROFILE_SEED_ENABLED:
        request_payload, profile_seed = _apply_profile_payload(request_payload, domain, version, request_hash)

    request_obj = _build_request(request_payload, request_cls, request_hash)

    extra_kwargs: dict[str, Any] = {}
    if profile_seed is not None:
        extra_kwargs["profile_seed"] = profile_seed

    response = generator(request_obj, **extra_kwargs)

    validate_payload(response, domain, "response", version, request_hash)

    canonical_response = canonical_json(response)
    return json.loads(canonical_response.decode("utf-8"))


def _build_request(payload: dict[str, Any], request_cls: Any, request_hash: str) -> Any:
    kwargs: dict[str, Any] = {"request_hash": request_hash}
    for field in fields(request_cls):
        if field.name == "request_hash":
            continue
        if field.name == "constraints" and "constraints" in payload:
            kwargs[field.name] = payload["constraints"] or {}
        elif field.name in payload:
            kwargs[field.name] = payload[field.name]
    return request_cls(**kwargs)


def _apply_profile_payload(
    payload: dict[str, Any],
    domain: str,
    version: str,
    request_hash: str,
) -> tuple[dict[str, Any], int | None]:
    profile_id = payload.get("profile_id")
    component_id = payload.get("component_id")

    if profile_id is not None and component_id is not None:
        raise DomainError(
            code="invalid_profile_selector",
            message="Provide either profile_id or component_id, not both",
            hint="Remove one of the identifiers before retrying.",
            path="/component_id",
            request_hash=request_hash,
        )

    if profile_id is None and component_id is None:
        return payload, None

    updated = dict(payload)

    if component_id is not None:
        if not isinstance(component_id, str) or not component_id:
            raise DomainError(
                code="invalid_component_id",
                message="component_id must be a non-empty string",
                hint="Example: 'urban_adult'",
                path="/component_id",
                request_hash=request_hash,
            )
        resolved_profile_id, extra_constraints = resolve_component_profile(
            locale=payload["locale"],
            version=version,
            component_id=component_id,
            request_hash=request_hash,
        )
        updated["profile_id"] = resolved_profile_id
        base_constraints = updated.get("constraints") or {}
        merged_constraints = _merge_constraints(base_constraints, extra_constraints)
        updated["constraints"] = merged_constraints
        facet = component_id
    else:
        if not isinstance(profile_id, str) or not profile_id:
            raise DomainError(
                code="invalid_profile_id",
                message="profile_id must be a non-empty string",
                hint="Example: 'urban_adult'",
                path="/profile_id",
                request_hash=request_hash,
            )
        updated["profile_id"] = profile_id
        facet = "profile"

    seed = derive_profile_seed(domain, updated["profile_id"], facet)
    return updated, seed


def _merge_constraints(base: Any, extra: Any) -> Any:
    if not isinstance(base, dict) or not isinstance(extra, dict):
        return extra
    merged: dict[str, Any] = dict(base)
    for key, value in extra.items():
        if key in merged:
            merged[key] = _merge_constraints(merged[key], value)
        else:
            merged[key] = value
    return merged
