from __future__ import annotations

from typing import Dict, List

from datamimic_ce.domains.determinism import canonical_json
from datamimic_ce.domains.facade import generate_domain

SEEDS: List[str] = ["alpha", "beta", "gamma", "delta"]
DOMAINS: List[str] = ["person", "address", "patient", "doctor"]


def test_property_seed_repeatability() -> None:
    for domain in DOMAINS:
        for seed in SEEDS:
            req: Dict[str, object] = {
                "domain": domain,
                "version": "v1",
                "count": 2,
                "seed": seed,
                "locale": "en_US",
                "clock": "2025-01-01T00:00:00Z",
            }
            first = generate_domain(req)
            second = generate_domain(req)
            assert canonical_json(first) == canonical_json(second)
