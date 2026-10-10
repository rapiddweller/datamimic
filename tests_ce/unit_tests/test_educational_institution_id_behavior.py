from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256
from random import Random
from typing import TypeVar

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution
from datamimic_ce.domains.public_sector.services.educational_institution_service import (
    EDUCATIONAL_INSTITUTION_SCHEMA,
)

_T = TypeVar("_T")
_HEX = "0123456789ABCDEF"


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _institution(seed: int) -> tuple[EducationalInstitution, EducationalInstitutionGenerator, Random]:
    rng = Random(seed)
    generator = EducationalInstitutionGenerator(dataset="US", rng=rng)
    return EducationalInstitution(generator), generator, rng


class _ChoiceRandom(Random):
    def __init__(self, choice_values: Sequence[str]) -> None:
        super().__init__(0)
        self.choice_values = list(choice_values)
        self.choice_calls: list[tuple[str, ...]] = []
        self.fail_at: int | None = None

    def choice(self, sequence: Sequence[_T]) -> _T:
        self.choice_calls.append(tuple(sequence))
        if self.fail_at == len(self.choice_calls):
            raise RuntimeError("scripted ID draw failure")
        return self.choice_values.pop(0)  # type: ignore[return-value]


def test_institution_id_candidate_is_delegated_then_claimed_and_cached() -> None:
    events: list[object] = []

    class CandidateGenerator(EducationalInstitutionGenerator):
        def generate_institution_id_candidate(self) -> str:
            events.append("candidate")
            return "EDU-0012ABCD"

    class ClaimObservedInstitution(EducationalInstitution):
        def _claim_identifier(self, name: str, candidate: str) -> str:
            events.append(("claim", name, candidate))
            return super()._claim_identifier(name, candidate)

    institution = ClaimObservedInstitution(CandidateGenerator(dataset="US", rng=Random(1)))

    assert institution.institution_id == "EDU-0012ABCD"
    assert events == ["candidate", ("claim", "institution_id", "EDU-0012ABCD")]
    assert institution.institution_id == "EDU-0012ABCD"
    assert events == ["candidate", ("claim", "institution_id", "EDU-0012ABCD")]


def test_institution_id_uses_one_public_rng_lookup_and_eight_ordered_hex_choices() -> None:
    class SwitchingGenerator(EducationalInstitutionGenerator):
        def __init__(self, first: Random, replacement: Random) -> None:
            self.rng_reads = 0
            self.replacement = replacement
            super().__init__(dataset="US", rng=first)

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng if self.rng_reads == 1 else self.replacement

    first_rng = _ChoiceRandom(["0"] * 8)
    replacement_rng = _ChoiceRandom(["F"] * 8)
    generator = SwitchingGenerator(first_rng, replacement_rng)
    generator.rng_reads = 0
    institution = EducationalInstitution(generator)

    assert institution.institution_id == "EDU-00000000"
    cached_id = institution.institution_id
    assert cached_id == "EDU-00000000"
    assert institution.field_cache["institution_id"] is cached_id
    assert generator.rng_reads == 1
    assert first_rng.choice_calls == [tuple(_HEX)] * 8
    assert replacement_rng.choice_calls == []


def test_institution_id_preserves_edu_prefix_uppercase_and_leading_zeroes() -> None:
    rng = _ChoiceRandom(["0", "1", "A", "B", "C", "D", "E", "F"])
    institution = EducationalInstitution(EducationalInstitutionGenerator(dataset="US", rng=rng))

    assert institution.institution_id == "EDU-01ABCDEF"
    assert len(institution.institution_id.removeprefix("EDU-")) == 8


def test_unbound_institutions_allow_duplicate_id_candidates() -> None:
    rng = _ChoiceRandom(["0"] * 16)
    generator = EducationalInstitutionGenerator(dataset="US", rng=rng)
    first = EducationalInstitution(generator)
    second = EducationalInstitution(generator)

    assert first.institution_id == "EDU-00000000"
    assert second.institution_id == "EDU-00000000"
    assert len(rng.choice_calls) == 16


def test_bound_institution_collision_is_claimed_without_candidate_redraw() -> None:
    rng = _ChoiceRandom(["0", "0", "0", "0", "0", "0", "0", "9"] * 2)
    generator = EducationalInstitutionGenerator(dataset="US", rng=rng)
    registry = IdentifierRegistry()
    institutions = [EducationalInstitution(generator), EducationalInstitution(generator)]
    for institution in institutions:
        institution._bind_identifier_registry(
            registry,
            "EducationalInstitution",
            EDUCATIONAL_INSTITUTION_SCHEMA.fields,
            {},
        )

    assert [institution.institution_id for institution in institutions] == ["EDU-00000009", "EDU-0000000A"]
    assert len(rng.choice_calls) == 16
    assert rng.choice_calls == [tuple(_HEX)] * 16


def test_partial_id_draw_failure_retries_fresh_and_then_caches() -> None:
    rng = _ChoiceRandom(["0"] * 2 + ["1"] * 8)
    rng.fail_at = 3
    institution = EducationalInstitution(EducationalInstitutionGenerator(dataset="US", rng=rng))

    with pytest.raises(RuntimeError, match="scripted ID draw failure"):
        _ = institution.institution_id
    assert "institution_id" not in institution.field_cache

    rng.fail_at = None
    assert institution.institution_id == "EDU-11111111"
    assert institution.institution_id == "EDU-11111111"
    assert len(rng.choice_calls) == 11


def test_claim_failure_retries_candidate_generation_without_caching() -> None:
    rng = _ChoiceRandom(["0"] * 8 + ["1"] * 8)
    events: list[tuple[str, str]] = []

    class FailOnceInstitution(EducationalInstitution):
        claims = 0

        def _claim_identifier(self, name: str, candidate: str) -> str:
            self.claims += 1
            events.append((name, candidate))
            if self.claims == 1:
                raise RuntimeError("registry claim failed")
            return candidate

    institution = FailOnceInstitution(EducationalInstitutionGenerator(dataset="US", rng=rng))

    with pytest.raises(RuntimeError, match="registry claim failed"):
        _ = institution.institution_id
    assert "institution_id" not in institution.field_cache

    assert institution.institution_id == "EDU-11111111"
    assert institution.institution_id == "EDU-11111111"
    assert len(rng.choice_calls) == 16
    assert events == [("institution_id", "EDU-00000000"), ("institution_id", "EDU-11111111")]


def test_seeded_id_first_and_name_programs_first_preserve_outputs_and_rng_states() -> None:
    id_first, _, id_first_rng = _institution(148)
    address = id_first.address
    assert _fingerprint(id_first_rng) == "6c8a57841a7522a975c909309c0abc344ddd653e358925a1e3df82914fc0e041"
    assert _fingerprint(address._row.city_generator.rng) == (
        "73bda386b6700bceaae3759c9576a4d4408b22e84f4a44b4cb03bf3cf7ffe894"
    )
    assert id_first.institution_id == "EDU-36F287DA"
    assert id_first.name == "Minneapolis Academy"
    assert id_first.programs == [
        "After-School Programs",
        "Arts and Music",
        "Early Childhood Education",
        "Gifted and Talented Program",
        "Math Fundamentals",
        "Science Discovery",
        "Special Education",
    ]
    assert id_first.level == "Elementary"
    assert _fingerprint(id_first_rng) == "9375d2915cdbd510c96a6b945429712e88d3ea04b9406a2b70c70fbebfe9ea35"
    assert _fingerprint(address._row.city_generator.rng) == (
        "6fc64d5b3ab438e334e017f7ab6751567d0058ea81e64f452b6dff772dee4a6e"
    )

    fields_first, _, fields_first_rng = _institution(148)
    fields_address = fields_first.address
    assert fields_first.name == "Minneapolis Middle School"
    assert fields_first.programs == [
        "Career Exploration",
        "Foreign Languages",
        "Mathematics",
        "Physical Education",
        "Science",
        "Social Studies",
        "Visual and Performing Arts",
    ]
    assert fields_first.level == "Middle School"
    assert fields_first.institution_id == "EDU-9080A528"
    assert _fingerprint(fields_first_rng) == "9375d2915cdbd510c96a6b945429712e88d3ea04b9406a2b70c70fbebfe9ea35"
    assert _fingerprint(fields_address._row.city_generator.rng) == (
        "6fc64d5b3ab438e334e017f7ab6751567d0058ea81e64f452b6dff772dee4a6e"
    )
