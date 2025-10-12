from __future__ import annotations

from datamimic_ce.domains.determinism import canonical_json
from datamimic_ce.domains.facade import generate_domain


def test_doctor_specialty_constraint() -> None:
    req = {
        "domain": "doctor",
        "version": "v1",
        "count": 3,
        "seed": "seed",
        "locale": "vi_VN",
        "constraints": {"specialty": "tim mạch", "license_prefix": "VN"},
        "clock": "2025-01-01T00:00:00Z",
    }
    response = generate_domain(req)
    assert len(response["items"]) == 3
    for item in response["items"]:
        assert item["specialty"].casefold() == "tim mạch".casefold()
        assert item["license_number"].startswith("VN-")


def test_doctor_determinism() -> None:
    req = {
        "domain": "doctor",
        "version": "v1",
        "count": 1,
        "seed": 123,
        "locale": "en_US",
        "clock": "2025-01-01T00:00:00Z",
    }
    r1 = generate_domain(req)
    r2 = generate_domain(req)
    assert canonical_json(r1) == canonical_json(r2)
