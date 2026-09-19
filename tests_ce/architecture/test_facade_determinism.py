"""
Facade determinism gate.

CE's determinism contract applies only to domains reachable through
``generate_domain(...)``. This gate enforces that contract: every
registered facade domain must produce byte-identical output for
identical input, and divergent output for different seeds.

Adding a new facade domain that breaks either invariant MUST break CI.

Out of scope: direct Service / Generator usage (best-effort per the
README) and full contract-enforced determinism across all generators,
services, and pipelines (Enterprise Platform).
"""

from __future__ import annotations

import platform

import pytest

from datamimic_ce.domains.facade import REGISTRY, generate_domain
from datamimic_ce.utils.version_util import get_datamimic_lib_version

REGISTERED_DOMAINS: list[str] = sorted({key[0] for key in REGISTRY})
EXPECTED_CONTENT_HASHES: dict[str, str] = {
    "address": "7d13e7a58d4a6258035436350ec7ecd043325ac46c5edbe039fa2797d4e169a0",
    "doctor": "2edec694c402cbc4f467858ea169a0888f5728ed2b7ce623632ee621e142c6a7",
    "patient": "906a07ea1c4d93ea52b2ba64139d2340e2d416c4b00a16e6448b61132bb93f89",
    "person": "e8365620df54a91427b02035004bf5315c637bde7e1df0706e1c641c857bd9d4",
}


def _request(domain: str, *, seed: str = "ci-determinism-gate", count: int = 3) -> dict:
    """Build a deterministic facade request for the given domain."""
    return {
        "domain": domain,
        "version": "v1",
        "count": count,
        "seed": seed,
        "locale": "en_US",
        "clock": "2026-01-01T00:00:00Z",
    }


@pytest.mark.parametrize("domain", REGISTERED_DOMAINS)
def test_facade_byte_identical_across_runs(domain: str) -> None:
    """Same seed + same model = byte-identical output (CE determinism contract)."""
    a = generate_domain(_request(domain))
    b = generate_domain(_request(domain))

    assert a["determinism_proof"]["content_hash"] == b["determinism_proof"]["content_hash"], (
        f"Facade domain {domain!r} breaks the CE determinism contract — "
        "two runs with identical input produced different content hashes."
    )
    assert a["items"] == b["items"], (
        f"Facade domain {domain!r}: content_hash matched but item payload diverged — investigate canonicalisation."
    )


@pytest.mark.parametrize("domain", REGISTERED_DOMAINS)
def test_facade_different_seed_diverges(domain: str) -> None:
    """Different seed must produce different output (RNG path is wired)."""
    a = generate_domain(_request(domain, seed="alpha"))
    b = generate_domain(_request(domain, seed="beta"))

    assert a["determinism_proof"]["content_hash"] != b["determinism_proof"]["content_hash"], (
        f"Facade domain {domain!r} produces identical output for different seeds — the RNG path is not wired through."
    )


@pytest.mark.parametrize("domain", REGISTERED_DOMAINS)
def test_facade_provenance_hash_present(domain: str) -> None:
    """Every facade response must carry a content_hash for re-executable lineage."""
    response = generate_domain(_request(domain, count=1))
    proof = response.get("determinism_proof")
    assert isinstance(proof, dict), f"Facade domain {domain!r}: response missing determinism_proof block."
    assert isinstance(proof.get("content_hash"), str) and len(proof["content_hash"]) >= 32, (
        f"Facade domain {domain!r}: determinism_proof.content_hash missing or too short."
    )
    assert proof["engine_version"] == get_datamimic_lib_version()
    assert proof["python_version"] == platform.python_version()
    assert proof["faker_version"] == get_datamimic_lib_version("faker")


@pytest.mark.parametrize("domain", sorted(EXPECTED_CONTENT_HASHES))
def test_facade_content_hash_matches_golden(domain: str) -> None:
    response = generate_domain(_request(domain))
    assert response["determinism_proof"]["content_hash"] == EXPECTED_CONTENT_HASHES[domain]


def test_facade_goldens_cover_every_registered_domain() -> None:
    assert set(EXPECTED_CONTENT_HASHES) == set(REGISTERED_DOMAINS)
