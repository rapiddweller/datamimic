from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _institution(seed: int) -> tuple[EducationalInstitution, EducationalInstitutionGenerator, Random]:
    rng = Random(seed)
    generator = EducationalInstitutionGenerator(dataset="US", rng=rng)
    return EducationalInstitution(generator), generator, rng


def test_student_and_staff_count_order_preserves_seeded_values_and_rng_state() -> None:
    students_first, _, students_first_rng = _institution(44)
    assert _rng_fingerprint(students_first_rng) == "092d529825b02dd3c7fdb06cc222d08f5df8c09d343b24154991ffea64fd6bad"
    assert students_first.type == "Public School"
    assert students_first.level == "Elementary"
    assert students_first.student_count == 209
    assert _rng_fingerprint(students_first_rng) == "baab853cce7da97c3e28256216369d8ce988608caf229e151a5400fd8ee17a57"
    assert students_first.staff_count == 18
    assert _rng_fingerprint(students_first_rng) == "9fe5a70450a522bb0aa3cdf4e99633a63b3b082adfebd046090f8a982a3245a8"

    staff_first, _, staff_first_rng = _institution(44)
    assert _rng_fingerprint(staff_first_rng) == "092d529825b02dd3c7fdb06cc222d08f5df8c09d343b24154991ffea64fd6bad"
    assert staff_first.staff_count == 18
    assert staff_first.type == "Public School"
    assert staff_first.level == "Elementary"
    assert staff_first.student_count == 209
    assert _rng_fingerprint(staff_first_rng) == "9fe5a70450a522bb0aa3cdf4e99633a63b3b082adfebd046090f8a982a3245a8"


@pytest.mark.parametrize(
    ("institution_type", "level", "bounds"),
    [
        ("University", "Graduate", (5000, 40000)),
        ("College", "Higher Education", (1000, 15000)),
        ("Public School", "Elementary", (200, 800)),
        ("Public School", "Middle School", (300, 1000)),
        ("Public School", "High School", (500, 2500)),
        ("Public School", "Other", (200, 1500)),
        ("Vocational Institute", "Career", (100, 5000)),
    ],
)
def test_student_count_branch_bounds_and_type_level_rng_order(
    institution_type: str, level: str, bounds: tuple[int, int]
) -> None:
    events: list[object] = []

    class BoundsRandom(Random):
        def __init__(self) -> None:
            super().__init__(1)
            self.randint_calls: list[tuple[int, int]] = []

        def randint(self, a: int, b: int) -> int:
            self.randint_calls.append((a, b))
            events.append(("randint", a, b))
            return a

    class RngObservedGenerator(EducationalInstitutionGenerator):
        rng_reads = 0

        @property
        def rng(self) -> Random:
            self.rng_reads += 1
            return self._rng

    class FixedInstitution(EducationalInstitution):
        @property
        def type(self) -> str:
            events.append("type")
            return institution_type

        @property
        def level(self) -> str:
            events.append("level")
            return level

    rng = BoundsRandom()
    generator = RngObservedGenerator(dataset="US", rng=rng)
    institution = FixedInstitution(generator)
    generator.rng_reads = 0
    events.clear()

    assert institution.student_count == bounds[0]
    assert generator.rng_reads == 1
    assert rng.randint_calls == [bounds]
    assert events == ["type", "level", ("randint", *bounds)]
    assert institution.student_count == bounds[0]
    assert generator.rng_reads == 1
    assert rng.randint_calls == [bounds]


def test_student_count_retries_after_rng_failure_without_caching() -> None:
    class FailOnceRandom(Random):
        def __init__(self) -> None:
            super().__init__(1)
            self.randint_calls: list[tuple[int, int]] = []
            self.fail_next = True

        def randint(self, a: int, b: int) -> int:
            self.randint_calls.append((a, b))
            if self.fail_next:
                self.fail_next = False
                raise RuntimeError("scripted student-count draw failure")
            return a

    rng = FailOnceRandom()
    generator = EducationalInstitutionGenerator(dataset="US", rng=rng)
    institution = EducationalInstitution(generator)
    institution._field_cache.update(type="University", level="Graduate")

    with pytest.raises(RuntimeError, match="scripted student-count draw failure"):
        _ = institution.student_count
    assert "student_count" not in institution.field_cache

    assert institution.student_count == 5000
    assert rng.randint_calls == [(5000, 40000), (5000, 40000)]


def test_student_count_generation_delegates_after_type_then_level() -> None:
    events: list[object] = []

    class CandidateGenerator(EducationalInstitutionGenerator):
        def generate_student_count(self, institution_type: str, level: str) -> int:
            events.append(("generate_student_count", institution_type, level))
            return 12345

    class EventInstitution(EducationalInstitution):
        @property
        def type(self) -> str:
            events.append("type")
            return "University"

        @property
        def level(self) -> str:
            events.append("level")
            return "Graduate"

    institution = EventInstitution(CandidateGenerator(dataset="US", rng=Random(44)))

    assert institution.student_count == 12345
    assert events == ["type", "level", ("generate_student_count", "University", "Graduate")]


class _StaffRandom(Random):
    def __init__(self, ratios: list[float | Exception], events: list[object]) -> None:
        super().__init__(44)
        self.ratios = ratios
        self.events = events

    def uniform(self, a: float, b: float) -> float:
        self.events.append(("uniform", a, b))
        ratio = self.ratios.pop(0)
        if isinstance(ratio, Exception):
            raise ratio
        return ratio


class _StaffObservedGenerator(EducationalInstitutionGenerator):
    def __init__(self, rng: Random, events: list[object]) -> None:
        self.events = events
        self.rng_reads = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        self.events.append("rng")
        return self._rng


class _StaffInputInstitution(EducationalInstitution):
    def __init__(
        self,
        generator: EducationalInstitutionGenerator,
        events: list[object],
        student_count: int,
        *,
        fail: bool = False,
    ) -> None:
        super().__init__(generator)
        self.events = events
        self._student_count = student_count
        self.fail = fail

    @property
    def student_count(self) -> int:
        self.events.append("student_count")
        if self.fail:
            raise RuntimeError("scripted student-count input failure")
        return self._student_count


@pytest.mark.parametrize(("student_count", "ratio", "expected"), [(199, 10.0, 19), (219, 25.0, 8), (0, 13.0, 5)])
def test_staff_count_resolves_students_then_draws_once_and_truncates_without_rounding(
    student_count: int,
    ratio: float,
    expected: int,
) -> None:
    events: list[object] = []
    generator = _StaffObservedGenerator(_StaffRandom([ratio], events), events)
    institution = _StaffInputInstitution(generator, events, student_count)

    assert institution.staff_count == expected
    assert events == ["student_count", "rng", ("uniform", 10, 25)]
    assert generator.rng_reads == 1
    state = generator._rng.getstate()
    assert institution.staff_count == expected
    assert generator._rng.getstate() == state
    assert generator.rng_reads == 1


def test_staff_count_student_failure_precedes_rng_lookup() -> None:
    events: list[object] = []
    generator = _StaffObservedGenerator(_StaffRandom([10.0], events), events)
    institution = _StaffInputInstitution(generator, events, 100, fail=True)

    with pytest.raises(RuntimeError, match="scripted student-count input failure"):
        _ = institution.staff_count
    assert "staff_count" not in institution.field_cache
    assert events == ["student_count"]
    assert generator.rng_reads == 0


def test_staff_count_draw_failure_is_uncached_and_retries_after_cached_students() -> None:
    events: list[object] = []
    rng = _StaffRandom([RuntimeError("scripted staff draw failure"), 10.0], events)
    generator = _StaffObservedGenerator(rng, events)
    institution = EducationalInstitution(generator)
    institution._field_cache["student_count"] = 200

    with pytest.raises(RuntimeError, match="scripted staff draw failure"):
        _ = institution.staff_count
    assert "staff_count" not in institution.field_cache
    assert generator.rng_reads == 1

    assert institution.staff_count == 20
    state = rng.getstate()
    assert institution.staff_count == 20
    assert rng.getstate() == state
    assert generator.rng_reads == 2
    assert events == [
        "rng",
        ("uniform", 10, 25),
        "rng",
        ("uniform", 10, 25),
    ]


def test_institutions_sharing_generator_cache_staff_independently() -> None:
    events: list[object] = []
    generator = _StaffObservedGenerator(_StaffRandom([10.0, 20.0], events), events)
    first = EducationalInstitution(generator)
    second = EducationalInstitution(generator)
    first._field_cache["student_count"] = 200
    second._field_cache["student_count"] = 200

    assert first.staff_count == 20
    assert first.staff_count == 20
    assert second.staff_count == 10
    assert second.staff_count == 10
    assert events == ["rng", ("uniform", 10, 25), "rng", ("uniform", 10, 25)]
    assert generator.rng_reads == 2


def test_staff_count_delegates_student_count_to_generator() -> None:
    events: list[object] = []

    class CandidateGenerator(_StaffObservedGenerator):
        def generate_staff_count(self, student_count: int) -> int:
            events.append(("generate_staff_count", student_count))
            return 14

    generator = CandidateGenerator(_StaffRandom([], events), events)
    institution = _StaffInputInstitution(generator, events, 140)

    assert institution.staff_count == 14
    assert events == ["student_count", ("generate_staff_count", 140)]
    assert generator.rng_reads == 0
