# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

import uuid
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry, _identifier_alternatives

KEY = ("Order", "order_id")
PREFIX_FORMAT = "ORD-[A-C]{2}"  # capacity 9: a sequence of picks runs into exhaustion
UUID_FORMAT = "uuid4"


def _reference_claim(
    seen_by_key: dict[tuple[str, str], set[str]],
    key: tuple[str, str],
    candidate: str,
    identifier_format: str,
) -> str:
    """The claim loop as it was before the fix: it replaces the set with a copy on every claim."""
    entity_name, name = key
    seen = seen_by_key.setdefault(key, set())
    if candidate not in seen:
        seen_by_key[key] = seen | {candidate}
        return candidate
    for alternative in _identifier_alternatives(identifier_format, candidate, len(seen)):
        if alternative not in seen:
            seen_by_key[key] = seen | {alternative}
            return alternative
    raise ValueError(f"Unique identifier space exhausted for {entity_name}.{name}")


def _candidate_pool(identifier_format: str, rng: Random) -> list[str]:
    if identifier_format == UUID_FORMAT:
        return [str(uuid.UUID(int=rng.getrandbits(128), version=4)) for _ in range(4)]
    return [f"ORD-{first}{second}" for first in "ABC" for second in "ABC"]


def _seeded_claims(identifier_format: str, seed: int, count: int) -> list[str]:
    rng = Random(seed)
    pool = _candidate_pool(identifier_format, rng)
    return [rng.choice(pool) for _ in range(count)]


@pytest.mark.parametrize("identifier_format", [UUID_FORMAT, PREFIX_FORMAT])
def test_seeded_claims_match_the_copying_reference(identifier_format: str) -> None:
    candidates = _seeded_claims(identifier_format, seed=639, count=40)

    registry = IdentifierRegistry()
    reference_seen: dict[tuple[str, str], set[str]] = {}
    actual: list[str] = []
    expected: list[str] = []
    for candidate in candidates:
        try:
            actual.append(registry.claim(*KEY, candidate, identifier_format))
        except ValueError as error:
            actual.append(f"error: {error}")
        try:
            expected.append(_reference_claim(reference_seen, KEY, candidate, identifier_format))
        except ValueError as error:
            expected.append(f"error: {error}")

    assert actual == expected
    assert registry._seen[KEY] == reference_seen[KEY]


def test_claim_mutates_the_seen_set_in_place() -> None:
    registry = IdentifierRegistry()
    registry.claim(*KEY, "ORD-AA", PREFIX_FORMAT)
    seen = registry._seen[KEY]

    # Fresh candidate, then a duplicate resolved to the next free rank (ORD-AC), then a duplicate
    # of ORD-AC resolved to ORD-BA: every claim goes through the set in place.
    for candidate in ("ORD-AB", "ORD-AA", "ORD-AC"):
        registry.claim(*KEY, candidate, PREFIX_FORMAT)
        assert registry._seen[KEY] is seen

    assert seen == {"ORD-AA", "ORD-AB", "ORD-AC", "ORD-BA"}
