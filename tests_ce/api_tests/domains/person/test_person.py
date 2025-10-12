from __future__ import annotations

import pytest

from datamimic_ce.domains.determinism import canonical_json, derive_seed, stable_uuid
from datamimic_ce.domains.facade import generate_domain
from datamimic_ce.domains.exceptions import DomainError


def test_determinism_person_minimal() -> None:
    req = {
        "domain": "person",
        "version": "v1",
        "count": 3,
        "seed": "abc",
        "locale": "de_DE",
        "clock": "2025-01-01T00:00:00Z",
    }
    r1 = generate_domain(req)
    r2 = generate_domain(req)
    assert canonical_json(r1) == canonical_json(r2)


def test_person_schema_valid() -> None:
    req = {
        "domain": "person",
        "version": "v1",
        "count": 2,
        "seed": "seed-42",
        "locale": "en_US",
        "constraints": {"sex": ["F", "M"], "age": {"min": 21, "max": 65}},
        "clock": "2025-01-01T00:00:00Z",
    }
    response = generate_domain(req)
    assert len(response["items"]) == 2
    for idx, item in enumerate(response["items"]):
        assert item["sex"] in {"F", "M"}
        assert 21 <= item["age"] <= 65
        expected_id = stable_uuid("datamimic:person:v1", derive_seed(req["seed"]), idx)
        assert item["id"] == expected_id


def test_person_locale_cycle_names() -> None:
    req = {
        "domain": "person",
        "version": "v1",
        "count": 4,
        "seed": "seed",
        "locale": "vi_VN",
        "clock": "2025-01-01T00:00:00Z",
    }
    response = generate_domain(req)
    locales = {item["locale"] for item in response["items"]}
    assert locales == {"vi_VN"}
    assert {item["sex"] for item in response["items"]} <= {"F", "M", "X"}


def test_person_unsupported_locale() -> None:
    req = {
        "domain": "person",
        "version": "v1",
        "count": 1,
        "seed": "seed",
        "locale": "fr_FR",
        "clock": "2025-01-01T00:00:00Z",
    }
    with pytest.raises(DomainError) as excinfo:
        generate_domain(req)
    assert excinfo.value.code == "unsupported_locale"
