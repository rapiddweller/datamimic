from __future__ import annotations

import json
from dataclasses import fields
from typing import TypeVar

from pydantic import JsonValue, TypeAdapter

from ..errors import DomainErrorCode
from ..errors.base import DomainError
from .healthcare.services.doctor_api import DoctorRequest
from .healthcare.services.doctor_api import generate as generate_doctor
from .healthcare.services.patient_api import PatientRequest
from .healthcare.services.patient_api import generate as generate_patient
from .shared.determinism import canonical_json, derive_profile_seed, hash_bytes
from .shared.json_types import JsonObject
from .shared.profile_components import resolve_component_profile
from .shared.schema_registry import validate_payload
from .shared.services.address_api import AddressRequest
from .shared.services.address_api import generate as generate_address
from .shared.services.person_api import PersonRequest
from .shared.services.person_api import generate as generate_person

RequestT = TypeVar("RequestT", bound=PersonRequest | AddressRequest | PatientRequest | DoctorRequest)

REGISTRY: tuple[tuple[str, str], ...] = (
    ("person", "v1"),
    ("address", "v1"),
    ("patient", "v1"),
    ("doctor", "v1"),
)

# Rule 5: facade orchestrates profile/component resolution to keep services pure.
PROFILE_SEED_ENABLED: tuple[tuple[str, str], ...] = (
    ("person", "v1"),
    ("patient", "v1"),
)


def generate_domain(payload: JsonValue) -> JsonObject:
    if not isinstance(payload, dict):
        raise DomainError(
            code=DomainErrorCode.INVALID_REQUEST,
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
            code=DomainErrorCode.INVALID_REQUEST,
            message="Missing or invalid 'domain' field",
            hint="Provide the target domain as a string",
            path="/domain",
            request_hash=request_hash,
        )
    if not isinstance(version, str):
        raise DomainError(
            code=DomainErrorCode.INVALID_REQUEST,
            message="Missing or invalid 'version' field",
            hint="Provide the target version as a string",
            path="/version",
            request_hash=request_hash,
        )

    key = (domain, version)
    if key not in REGISTRY:
        raise DomainError(
            code=DomainErrorCode.UNSUPPORTED_DOMAIN,
            message=f"Domain '{domain}' version '{version}' is not supported",
            hint=f"Supported domains: {sorted({registered_domain for registered_domain, _ in REGISTRY})}",
            path="/domain",
            request_hash=request_hash,
        )

    validate_payload(payload, domain, "request", version, request_hash)

    request_payload = dict(payload)
    profile_seed = None
    if key in PROFILE_SEED_ENABLED:
        request_payload, profile_seed = _apply_profile_payload(request_payload, domain, version, request_hash)

    if key == ("person", "v1"):
        person_request = _build_request(request_payload, PersonRequest, request_hash)
        response = (
            generate_person(person_request, profile_seed=profile_seed)
            if profile_seed is not None
            else generate_person(person_request)
        )
    elif key == ("address", "v1"):
        address_request = _build_request(request_payload, AddressRequest, request_hash)
        response = generate_address(address_request)
    elif key == ("patient", "v1"):
        patient_request = _build_request(request_payload, PatientRequest, request_hash)
        response = (
            generate_patient(patient_request, profile_seed=profile_seed)
            if profile_seed is not None
            else generate_patient(patient_request)
        )
    else:
        doctor_request = _build_request(request_payload, DoctorRequest, request_hash)
        response = generate_doctor(doctor_request)

    validate_payload(response, domain, "response", version, request_hash)
    canonical_response = canonical_json(response)
    return json.loads(canonical_response.decode("utf-8"))


def _build_request(payload: JsonObject, request_cls: type[RequestT], request_hash: str) -> RequestT:
    kwargs: dict[str, object] = {"request_hash": request_hash}
    for field in fields(request_cls):
        if field.name == "request_hash":
            continue
        if field.name == "constraints" and "constraints" in payload:
            kwargs[field.name] = payload["constraints"] or {}
        elif field.name in payload:
            kwargs[field.name] = payload[field.name]
    return TypeAdapter(request_cls).validate_python(kwargs)


def _apply_profile_payload(
    payload: JsonObject,
    domain: str,
    version: str,
    request_hash: str,
) -> tuple[JsonObject, int | None]:
    profile_id = payload.get("profile_id")
    component_id = payload.get("component_id")

    if profile_id is not None and component_id is not None:
        raise DomainError(
            code=DomainErrorCode.INVALID_PROFILE_SELECTOR,
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
                code=DomainErrorCode.INVALID_COMPONENT_ID,
                message="component_id must be a non-empty string",
                hint="Example: 'urban_adult'",
                path="/component_id",
                request_hash=request_hash,
            )
        locale = payload["locale"]
        assert isinstance(locale, str)
        resolved_profile_id, extra_constraints = resolve_component_profile(
            locale=locale,
            version=version,
            component_id=component_id,
            request_hash=request_hash,
        )
        updated["profile_id"] = resolved_profile_id
        base_constraints = updated.get("constraints") or {}
        updated["constraints"] = _merge_constraints(base_constraints, extra_constraints)
        facet = component_id
        selected_profile_id = resolved_profile_id
    else:
        if not isinstance(profile_id, str) or not profile_id:
            raise DomainError(
                code=DomainErrorCode.INVALID_PROFILE_ID,
                message="profile_id must be a non-empty string",
                hint="Example: 'urban_adult'",
                path="/profile_id",
                request_hash=request_hash,
            )
        updated["profile_id"] = profile_id
        facet = "profile"
        selected_profile_id = profile_id

    seed = derive_profile_seed(domain, selected_profile_id, facet)
    return updated, seed


def _merge_constraints(base: JsonValue, extra: JsonValue) -> JsonValue:
    if not isinstance(base, dict) or not isinstance(extra, dict):
        return extra
    merged = dict(base)
    for key, value in extra.items():
        if key in merged:
            merged[key] = _merge_constraints(merged[key], value)
        else:
            merged[key] = value
    return merged
