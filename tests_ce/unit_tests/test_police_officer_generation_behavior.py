from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.domain_core.base_entity import IdentifierRegistry
from datamimic_ce.domains.public_sector.generators.police_officer_generator import PoliceOfficerGenerator
from datamimic_ce.domains.public_sector.models.police_officer import PoliceOfficer
from datamimic_ce.domains.public_sector.services.police_officer_service import POLICE_OFFICER_SCHEMA

_REFERENCE_NOW = datetime(2026, 9, 29, 10, 30, tzinfo=timezone.utc)


class _TraceRandom(Random):
    def __init__(self, values: list[int]) -> None:
        super().__init__(0)
        self.values = iter(values)
        self.calls: list[tuple[int, int]] = []
        self.fail_next = False

    def randint(self, a: int, b: int) -> int:
        self.calls.append((a, b))
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("scripted badge draw failure")
        return next(self.values)


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _officer(seed: int) -> tuple[PoliceOfficer, PoliceOfficerGenerator, Random]:
    rng = Random(seed)
    generator = PoliceOfficerGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    return PoliceOfficer(generator), generator, rng


class _ChoiceTraceRandom(Random):
    def __init__(self, values: list[str]) -> None:
        super().__init__(0)
        self.values = iter(values)
        self.calls: list[str] = []
        self.fail_next = False

    def choice(self, seq: str) -> str:
        self.calls.append(seq)
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError("scripted officer ID draw failure")
        return next(self.values)


def test_badge_number_uses_public_rng_once_with_four_ordered_digit_draws_and_caches() -> None:
    class RngObservedGenerator(PoliceOfficerGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    rng = _TraceRandom([0, 1, 2, 3])
    generator = RngObservedGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    officer = PoliceOfficer(generator)
    generator.rng_reads = 0

    assert officer.badge_number == "0123"
    assert rng.calls == [(0, 9)] * 4
    assert generator.rng_reads == 1
    assert officer.badge_number == "0123"
    assert rng.calls == [(0, 9)] * 4
    assert generator.rng_reads == 1


def test_badge_numbers_are_not_claimed_and_caches_are_per_officer_on_shared_generator() -> None:
    rng = _TraceRandom([0] * 8)
    generator = PoliceOfficerGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    first, second = PoliceOfficer(generator), PoliceOfficer(generator)

    assert first.badge_number == "0000"
    assert second.badge_number == "0000"
    assert len(rng.calls) == 8
    assert first.badge_number == "0000"
    assert second.badge_number == "0000"
    assert len(rng.calls) == 8


def test_badge_number_retries_after_draw_failure_without_caching_partial_result() -> None:
    rng = _TraceRandom([1, 2, 3, 4])
    generator = PoliceOfficerGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    officer = PoliceOfficer(generator)
    rng.fail_next = True

    with pytest.raises(RuntimeError, match="scripted badge draw failure"):
        _ = officer.badge_number
    assert "badge_number" not in officer.field_cache

    assert officer.badge_number == "1234"
    assert rng.calls == [(0, 9)] * 5
    assert officer.badge_number == "1234"
    assert rng.calls == [(0, 9)] * 5


def test_badge_number_and_officer_id_access_order_preserves_seeded_values_and_rng_state() -> None:
    badge_first, _, badge_first_rng = _officer(613)
    assert _rng_fingerprint(badge_first_rng) == "e31c37a3acf786e8b38b058522b9dba4e70acb8eb68665c59cae10a2faed431b"
    assert badge_first.badge_number == "1986"
    assert _rng_fingerprint(badge_first_rng) == "ea1646c7dcd8849b780cccede050b9b4bb12a56dccae949be8e141cf4238eef9"
    assert badge_first.officer_id == "OFF-FA3D0DDA"
    assert _rng_fingerprint(badge_first_rng) == "df12387e4229193b79d0a8ded15fc7f2e3f2fb00cbee003acfb25bfde9ba7352"

    officer_id_first, _, officer_id_first_rng = _officer(613)
    assert _rng_fingerprint(officer_id_first_rng) == "e31c37a3acf786e8b38b058522b9dba4e70acb8eb68665c59cae10a2faed431b"
    assert officer_id_first.officer_id == "OFF-3CFA3D0D"
    assert _rng_fingerprint(officer_id_first_rng) == "82430da19d824f2767810cf1f0b75bc3deaa3891fee9fcfdfaeeb6062e40906b"
    assert officer_id_first.badge_number == "9685"
    assert _rng_fingerprint(officer_id_first_rng) == "df12387e4229193b79d0a8ded15fc7f2e3f2fb00cbee003acfb25bfde9ba7352"


def test_badge_number_candidate_generation_delegates_to_generator() -> None:
    class CandidateGenerator(PoliceOfficerGenerator):
        calls = 0

        def generate_badge_number(self) -> str:
            self.calls += 1
            return "0420"

    generator = CandidateGenerator(dataset="US", rng=Random(41), reference_now=_REFERENCE_NOW)
    officer = PoliceOfficer(generator)

    assert officer.badge_number == "0420"
    assert generator.calls == 1


def test_officer_id_uses_public_rng_once_with_eight_ordered_hex_choices_and_caches() -> None:
    class RngObservedGenerator(PoliceOfficerGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    rng = _ChoiceTraceRandom(["0", "0", "0", "0", "0", "0", "A", "F"])
    generator = RngObservedGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    officer = PoliceOfficer(generator)
    generator.rng_reads = 0

    assert officer.officer_id == "OFF-000000AF"
    assert rng.calls == ["0123456789ABCDEF"] * 8
    assert generator.rng_reads == 1
    assert officer.officer_id == "OFF-000000AF"
    assert rng.calls == ["0123456789ABCDEF"] * 8
    assert generator.rng_reads == 1


def test_unbound_officers_may_keep_duplicate_id_candidates() -> None:
    values = ["0"] * 8 + ["0"] * 8
    rng = _ChoiceTraceRandom(values)
    generator = PoliceOfficerGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    first, second = PoliceOfficer(generator), PoliceOfficer(generator)

    assert first.officer_id == "OFF-00000000"
    assert second.officer_id == "OFF-00000000"
    assert rng.calls == ["0123456789ABCDEF"] * 16
    assert first.officer_id == "OFF-00000000"
    assert second.officer_id == "OFF-00000000"
    assert rng.calls == ["0123456789ABCDEF"] * 16


def test_bound_officer_id_collision_is_claimed_without_redrawing() -> None:
    values = ["0"] * 7 + ["9"]
    rng = _ChoiceTraceRandom(values * 2)
    generator = PoliceOfficerGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    registry = IdentifierRegistry()
    first, second = PoliceOfficer(generator), PoliceOfficer(generator)
    for officer in (first, second):
        officer._bind_identifier_registry(registry, "PoliceOfficer", POLICE_OFFICER_SCHEMA.fields, {})

    assert first.officer_id == "OFF-00000009"
    assert second.officer_id == "OFF-0000000A"
    assert rng.calls == ["0123456789ABCDEF"] * 16


def test_officer_id_retries_after_rng_failure_without_caching_partial_result() -> None:
    rng = _ChoiceTraceRandom(["0"] * 8)
    generator = PoliceOfficerGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    officer = PoliceOfficer(generator)
    rng.fail_next = True

    with pytest.raises(RuntimeError, match="scripted officer ID draw failure"):
        _ = officer.officer_id
    assert "officer_id" not in officer.field_cache

    assert officer.officer_id == "OFF-00000000"
    assert rng.calls == ["0123456789ABCDEF"] * 9
    assert officer.officer_id == "OFF-00000000"
    assert rng.calls == ["0123456789ABCDEF"] * 9


def test_officer_id_retries_generation_after_claim_failure() -> None:
    class ClaimFailsOncePoliceOfficer(PoliceOfficer):
        claim_calls = 0

        def _claim_identifier(self, name: str, candidate: str) -> str:
            self.claim_calls += 1
            if self.claim_calls == 1:
                raise RuntimeError("scripted claim failure")
            return super()._claim_identifier(name, candidate)

    rng = _ChoiceTraceRandom(["0"] * 16)
    generator = PoliceOfficerGenerator(dataset="US", rng=rng, reference_now=_REFERENCE_NOW)
    officer = ClaimFailsOncePoliceOfficer(generator)

    with pytest.raises(RuntimeError, match="scripted claim failure"):
        _ = officer.officer_id
    assert "officer_id" not in officer.field_cache

    assert officer.officer_id == "OFF-00000000"
    assert rng.calls == ["0123456789ABCDEF"] * 16
    assert officer.claim_calls == 2


def test_officer_id_candidate_creation_delegates_to_generator() -> None:
    class CandidateGenerator(PoliceOfficerGenerator):
        calls = 0

        def generate_officer_id_candidate(self) -> str:
            self.calls += 1
            return "OFF-00000042"

    generator = CandidateGenerator(dataset="US", rng=Random(613), reference_now=_REFERENCE_NOW)
    officer = PoliceOfficer(generator)

    assert officer.officer_id == "OFF-00000042"
    assert generator.calls == 1
