import pytest

from datamimic_ce.domains.facade import _build_request, generate_domain
from datamimic_ce.domains.healthcare.services.doctor_api import DoctorRequest
from datamimic_ce.domains.healthcare.services.patient_api import PatientRequest
from datamimic_ce.domains.shared.determinism import canonical_json, hash_bytes
from datamimic_ce.domains.shared.json_types import JsonObject
from datamimic_ce.domains.shared.services.address_api import AddressRequest
from datamimic_ce.domains.shared.services.person_api import PersonRequest
from datamimic_ce.errors import DomainErrorCode
from datamimic_ce.errors.base import DomainError


def test_request_builder_matches_all_domain_dataclass_constructors() -> None:
    request_hash = "request-hash"
    clock = "2025-01-02T03:04:05Z"

    person_payload: JsonObject = {
        "count": 3,
        "seed": "person-seed",
        "locale": "en_US",
        "profile_id": "adult",
        "constraints": {"sex": ["F"], "age": {"min": 18, "max": 30}},
        "clock": clock,
    }
    assert _build_request(person_payload, PersonRequest, request_hash) == PersonRequest(
        count=3,
        seed="person-seed",
        locale="en_US",
        profile_id="adult",
        constraints={"sex": ["F"], "age": {"min": 18, "max": 30}},
        clock=clock,
        request_hash=request_hash,
    )

    address_payload: JsonObject = {
        "count": 2,
        "seed": 12,
        "locale": "en_US",
        "constraints": {"country": "US", "postal_code_prefix": 9},
        "clock": clock,
    }
    assert _build_request(address_payload, AddressRequest, request_hash) == AddressRequest(
        count=2,
        seed=12,
        locale="en_US",
        constraints={"country": "US", "postal_code_prefix": 9},
        clock=clock,
        request_hash=request_hash,
    )

    patient_payload: JsonObject = {
        "count": 1,
        "seed": "patient-seed",
        "locale": "en_US",
        "component_id": "urban_adult",
        "constraints": {"age": {"min": 20}, "conditions": ["HTN"]},
        "clock": clock,
    }
    assert _build_request(patient_payload, PatientRequest, request_hash) == PatientRequest(
        count=1,
        seed="patient-seed",
        locale="en_US",
        component_id="urban_adult",
        constraints={"age": {"min": 20}, "conditions": ["HTN"]},
        clock=clock,
        request_hash=request_hash,
    )

    doctor_payload: JsonObject = {
        "count": 4,
        "seed": 6,
        "locale": "en_US",
        "constraints": {"specialty": ["Cardiology"], "license_prefix": "LIC"},
        "clock": clock,
    }
    assert _build_request(doctor_payload, DoctorRequest, request_hash) == DoctorRequest(
        count=4,
        seed=6,
        locale="en_US",
        constraints={"specialty": ["Cardiology"], "license_prefix": "LIC"},
        clock=clock,
        request_hash=request_hash,
    )


def test_facade_rejects_invalid_payload_before_request_building() -> None:
    payload: JsonObject = {
        "domain": "person",
        "version": "v1",
        "count": 1,
        "seed": 0,
        "locale": "not-a-locale",
        "clock": "2025-01-02T03:04:05Z",
    }

    with pytest.raises(DomainError) as error:
        generate_domain(payload)
    assert error.value.code is DomainErrorCode.SCHEMA_VALIDATION_FAILED
    assert error.value.to_dict()["code"] == "schema_validation_failed"
    assert error.value.path == "/locale"
    assert error.value.request_hash == hash_bytes(canonical_json(payload))
