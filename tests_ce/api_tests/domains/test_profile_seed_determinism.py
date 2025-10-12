"""Profile seed cascade regression tests (rules 4-6)."""
from datamimic_ce.domains.determinism import canonical_json
from datamimic_ce.domains.facade import generate_domain


def test_profile_id_repeatable() -> None:
    req = {
        "domain": "person",
        "version": "v1",
        "count": 3,
        "seed": "cascade-1",
        "locale": "en_US",
        "clock": "2025-01-01T00:00:00Z",
        "profile_id": "urban_adult",
    }
    first = generate_domain(req)
    second = generate_domain(req)
    assert canonical_json(first) == canonical_json(second)


def test_component_id_repeatable() -> None:
    req = {
        "domain": "person",
        "version": "v1",
        "count": 2,
        "seed": "cascade-2",
        "locale": "en_US",
        "clock": "2025-01-01T00:00:00Z",
        "component_id": "urban_adult",
    }
    first = generate_domain(req)
    second = generate_domain(req)
    assert canonical_json(first) == canonical_json(second)
