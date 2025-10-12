from __future__ import annotations

from datamimic_ce.domains.determinism import canonical_json, derive_seed, stable_uuid
from datamimic_ce.domains.facade import generate_domain


def test_patient_cross_entity_consistency() -> None:
    req = {
        "domain": "patient",
        "version": "v1",
        "count": 2,
        "seed": "clinic-42#demo",
        "locale": "de_DE",
        "constraints": {"conditions": ["I10"], "id_namespace": "clinic-42"},
        "clock": "2025-01-01T00:00:00Z",
    }
    response = generate_domain(req)
    derived = derive_seed(req["seed"])
    for idx, item in enumerate(response["items"]):
        assert item["person_id"] == stable_uuid("datamimic:person:v1", derived, idx)
        assert item["address_id"] == stable_uuid("datamimic:address:v1", derived, idx)
        assert item["primary_condition"] == "I10"
        assert item["human_id"].startswith("CLINIC-42-")


def test_patient_determinism() -> None:
    req = {
        "domain": "patient",
        "version": "v1",
        "count": 3,
        "seed": "repeat",
        "locale": "en_US",
        "clock": "2025-01-01T00:00:00Z",
    }
    r1 = generate_domain(req)
    r2 = generate_domain(req)
    assert canonical_json(r1) == canonical_json(r2)
