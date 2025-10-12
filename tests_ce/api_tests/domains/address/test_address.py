from __future__ import annotations

from datamimic_ce.domains.determinism import canonical_json
from datamimic_ce.domains.facade import generate_domain


def test_determinism_address_zero_count() -> None:
    req = {
        "domain": "address",
        "version": "v1",
        "count": 0,
        "seed": "seed",
        "locale": "en_US",
        "clock": "2025-01-01T00:00:00Z",
    }
    r1 = generate_domain(req)
    r2 = generate_domain(req)
    assert canonical_json(r1) == canonical_json(r2)
    assert r1["items"] == []


def test_address_postal_prefix() -> None:
    req = {
        "domain": "address",
        "version": "v1",
        "count": 2,
        "seed": "seed",
        "locale": "de_DE",
        "constraints": {"postal_code_prefix": "80"},
        "clock": "2025-01-01T00:00:00Z",
    }
    response = generate_domain(req)
    for item in response["items"]:
        assert item["postal_code"].startswith("80")
        assert len(item["postal_code"]) == 5
        assert item["country"] == "DE"
