from __future__ import annotations

from collections.abc import Sequence
from hashlib import sha256
from random import Random
from typing import TypeVar

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice
from datamimic_ce.domains.public_sector.services.administration_office_service import ADMINISTRATION_OFFICE_SCHEMA

_T = TypeVar("_T")
_HEX = "0123456789ABCDEF"


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _office(seed: int) -> tuple[AdministrationOffice, AdministrationOfficeGenerator, Random]:
    rng = Random(seed)
    generator = AdministrationOfficeGenerator(dataset="US", rng=rng)
    return AdministrationOffice(generator), generator, rng


class _ChoiceRandom(Random):
    def __init__(self, choice_values: Sequence[str], events: list[object] | None = None) -> None:
        super().__init__(0)
        self.choice_values = list(choice_values)
        self.events = events if events is not None else []
        self.choice_calls: list[tuple[str, ...]] = []
        self.fail_at: int | None = None

    def choice(self, sequence: Sequence[_T]) -> _T:
        self.choice_calls.append(tuple(sequence))
        self.events.append(("choice", tuple(sequence)))
        if self.fail_at == len(self.choice_calls):
            raise RuntimeError("scripted ID draw failure")
        return self.choice_values.pop(0)  # type: ignore[return-value]


def test_office_id_candidate_is_delegated_then_claimed() -> None:
    events: list[object] = []

    class CandidateGenerator(AdministrationOfficeGenerator):
        def generate_office_id_candidate(self) -> str:
            events.append("candidate")
            return "ADM-0012ABCD"

    class ClaimObservedOffice(AdministrationOffice):
        def _claim_identifier(self, name: str, candidate: str) -> str:
            events.append(("claim", name, candidate))
            return super()._claim_identifier(name, candidate)

    office = ClaimObservedOffice(CandidateGenerator(dataset="US", rng=Random(1)))

    assert office.office_id == "ADM-0012ABCD"
    assert events == ["candidate", ("claim", "office_id", "ADM-0012ABCD")]
    assert office.office_id == "ADM-0012ABCD"
    assert events == ["candidate", ("claim", "office_id", "ADM-0012ABCD")]


def test_office_id_draws_eight_hex_digits_once_through_public_rng_and_caches() -> None:
    class SwitchingGenerator(AdministrationOfficeGenerator):
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
    office = AdministrationOffice(generator)

    assert office.office_id == "ADM-00000000"
    assert office.office_id == "ADM-00000000"
    assert generator.rng_reads == 1
    assert first_rng.choice_calls == [tuple(_HEX)] * 8
    assert replacement_rng.choice_calls == []


def test_office_id_preserves_prefix_uppercase_and_leading_zeroes() -> None:
    rng = _ChoiceRandom(["0", "1", "A", "B", "C", "D", "E", "F"])
    office = AdministrationOffice(AdministrationOfficeGenerator(dataset="US", rng=rng))

    assert office.office_id == "ADM-01ABCDEF"
    assert len(office.office_id.removeprefix("ADM-")) == 8


def test_unbound_offices_allow_duplicate_candidates() -> None:
    rng = _ChoiceRandom(["0"] * 16)
    generator = AdministrationOfficeGenerator(dataset="US", rng=rng)
    first = AdministrationOffice(generator)
    second = AdministrationOffice(generator)

    assert first.office_id == "ADM-00000000"
    assert second.office_id == "ADM-00000000"
    assert len(rng.choice_calls) == 16


def test_bound_office_collision_is_allocated_by_claim_without_redraw() -> None:
    events: list[object] = []
    rng = _ChoiceRandom(["0", "0", "0", "0", "0", "0", "0", "9"] * 2, events)
    generator = AdministrationOfficeGenerator(dataset="US", rng=rng)
    registry = IdentifierRegistry()

    class ClaimObservedOffice(AdministrationOffice):
        def _claim_identifier(self, name: str, candidate: str) -> str:
            events.append(("claim", candidate))
            return super()._claim_identifier(name, candidate)

    offices = [ClaimObservedOffice(generator), ClaimObservedOffice(generator)]
    for office in offices:
        office._bind_identifier_registry(registry, "AdministrationOffice", ADMINISTRATION_OFFICE_SCHEMA.fields, {})

    assert [office.office_id for office in offices] == ["ADM-00000009", "ADM-0000000A"]
    assert len(rng.choice_calls) == 16
    assert events == [
        *( [("choice", tuple(_HEX))] * 8 ),
        ("claim", "ADM-00000009"),
        *( [("choice", tuple(_HEX))] * 8 ),
        ("claim", "ADM-00000009"),
    ]


def test_partial_id_draw_failure_retries_fresh_and_success_is_cached() -> None:
    rng = _ChoiceRandom(["0"] * 2 + ["1"] * 8)
    rng.fail_at = 3
    office = AdministrationOffice(AdministrationOfficeGenerator(dataset="US", rng=rng))

    with pytest.raises(RuntimeError, match="scripted ID draw failure"):
        _ = office.office_id
    assert "office_id" not in office.field_cache

    rng.fail_at = None
    assert office.office_id == "ADM-11111111"
    assert office.office_id == "ADM-11111111"
    assert len(rng.choice_calls) == 11


def test_claim_failure_retries_candidate_generation_without_caching() -> None:
    events: list[object] = []
    rng = _ChoiceRandom(["0"] * 8 + ["1"] * 8, events)

    class FailOnceOffice(AdministrationOffice):
        claims = 0

        def _claim_identifier(self, name: str, candidate: str) -> str:
            self.claims += 1
            events.append(("claim", candidate))
            if self.claims == 1:
                raise RuntimeError("registry claim failed")
            return candidate

    office = FailOnceOffice(AdministrationOfficeGenerator(dataset="US", rng=rng))

    with pytest.raises(RuntimeError, match="registry claim failed"):
        _ = office.office_id
    assert "office_id" not in office.field_cache

    assert office.office_id == "ADM-11111111"
    assert office.office_id == "ADM-11111111"
    assert len(rng.choice_calls) == 16
    assert events == [
        *( [("choice", tuple(_HEX))] * 8 ),
        ("claim", "ADM-00000000"),
        *( [("choice", tuple(_HEX))] * 8 ),
        ("claim", "ADM-11111111"),
    ]


def test_seeded_office_id_first_and_jurisdiction_name_first_preserve_outputs_and_rng_states() -> None:
    id_first, _, id_first_rng = _office(702)
    assert _fingerprint(id_first_rng) == "6ad531060ed16022ea47737fe05019de4f633f9b17d93f76aa93e5c77cac55a9"
    assert id_first.office_id == "ADM-9ED2875F"
    assert id_first.jurisdiction == "State of IN"
    assert id_first.name == "State of IN Government Office"
    assert id_first.website == "https://www.in.gov"
    assert _fingerprint(id_first_rng) == "ed6a5f9f73deea3892fdec546bbcaba9f217b7fcbc777f3cbedd6f8664759daf"

    fields_first, _, fields_first_rng = _office(702)
    assert fields_first.jurisdiction == "Federal"
    assert fields_first.name == "IN Elections Office Department"
    assert fields_first.website == "https://www.federal.gov"
    assert fields_first.office_id == "ADM-D2875F42"
    assert _fingerprint(fields_first_rng) == "0aac79dcb576a216186556c623e504d11c6c5480f58ed0db271cad76669de536"
