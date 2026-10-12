from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from random import Random

import pytest

from datamimic_ce.domains.public_sector import models as institution_models
from datamimic_ce.domains.public_sector.generators.educational_institution_generator import (
    EducationalInstitutionGenerator,
)
from datamimic_ce.domains.public_sector.models.educational_institution import EducationalInstitution


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _institution(seed: int) -> tuple[EducationalInstitution, EducationalInstitutionGenerator, Random]:
    rng = Random(seed)
    generator = EducationalInstitutionGenerator(dataset="US", rng=rng)
    return EducationalInstitution(generator), generator, rng


@pytest.mark.parametrize(
    ("level", "expected_slug"),
    [
        ("Elementary Middle High Higher Education Vocational", "elementary"),
        ("Middle High", "middle_school"),
        ("High School", "high_school"),
        ("Higher Education", "high_school"),
        ("Undergraduate", "higher_education"),
        ("Postgraduate", "higher_education"),
        ("Vocational Technical", "vocational"),
        ("Technical", "vocational"),
        ("Unknown", "k12"),
        ("elementary", "k12"),
    ],
)
def test_generate_programs_maps_level_with_exact_precedence_and_case(
    level: str, expected_slug: str
) -> None:
    events: list[object] = []
    start = Path("/fixture/institution.py")

    class RecordingGenerator(EducationalInstitutionGenerator):
        def pick_programs(self, slug: str, *, start: Path) -> list[str]:
            events.append((slug, start))
            return [slug]

    generator = RecordingGenerator(dataset="US", rng=Random(1))

    assert generator.generate_programs(level, start=start) == [expected_slug]
    assert events == [(expected_slug, start)]


def test_programs_resolves_level_before_generator_and_forwards_model_path() -> None:
    events: list[object] = []

    class CandidateGenerator(EducationalInstitutionGenerator):
        def generate_programs(self, level: str, *, start: Path) -> list[str]:
            events.append(("generate_programs", level, start))
            return ["Reading"]

        def pick_programs(self, slug: str, *, start: Path) -> list[str]:
            events.append(("pick_programs", slug, start))
            return [slug]

    class EventInstitution(EducationalInstitution):
        @property
        def level(self) -> str:
            events.append("level")
            return "Elementary"

    institution = EventInstitution(CandidateGenerator(dataset="US", rng=Random(1)))

    assert institution.programs == ["Reading"]
    assert events == [
        "level",
        ("generate_programs", "Elementary", Path(institution_models.educational_institution.__file__)),
    ]


def test_level_failure_prevents_program_generation_and_leaves_property_uncached() -> None:
    events: list[object] = []

    class CandidateGenerator(EducationalInstitutionGenerator):
        def generate_programs(self, level: str, *, start: Path) -> list[str]:
            events.append(("generate_programs", level, start))
            return ["Reading"]

    class FailsOnceInstitution(EducationalInstitution):
        level_reads = 0

        @property
        def level(self) -> str:
            self.level_reads += 1
            events.append("level")
            if self.level_reads == 1:
                raise RuntimeError("level resolution failed")
            return "Elementary"

    institution = FailsOnceInstitution(CandidateGenerator(dataset="US", rng=Random(1)))

    with pytest.raises(RuntimeError, match="level resolution failed"):
        _ = institution.programs
    assert "programs" not in institution.field_cache
    assert events == ["level"]

    assert institution.programs == ["Reading"]
    assert events == [
        "level",
        "level",
        ("generate_programs", "Elementary", Path(institution_models.educational_institution.__file__)),
    ]


def test_programs_cache_result_identity_and_keep_entity_lists_independent() -> None:
    class FreshListGenerator(EducationalInstitutionGenerator):
        def __init__(self) -> None:
            super().__init__(dataset="US", rng=Random(2))
            self.calls = 0

        def pick_programs(self, slug: str, *, start: Path) -> list[str]:  # noqa: ARG002
            self.calls += 1
            return [f"program-{self.calls}"]

    generator = FreshListGenerator()
    first = EducationalInstitution(generator)
    second = EducationalInstitution(generator)
    first._field_cache["level"] = "Elementary"
    second._field_cache["level"] = "Elementary"

    first_programs = first.programs
    assert first.programs is first_programs
    second_programs = second.programs
    assert second.programs is second_programs
    assert first_programs == ["program-1"]
    assert second_programs == ["program-2"]
    assert first_programs is not second_programs

    first_programs.append("local mutation")
    assert second.programs == ["program-2"]
    assert generator.calls == 2


def test_programs_failure_is_uncached_and_retries_same_level() -> None:
    events: list[object] = []

    class FailOnceGenerator(EducationalInstitutionGenerator):
        def pick_programs(self, slug: str, *, start: Path) -> list[str]:
            events.append((slug, start))
            if len(events) == 1:
                raise RuntimeError("program dataset failed")
            return ["Reading"]

    generator = FailOnceGenerator(dataset="US", rng=Random(3))
    institution = EducationalInstitution(generator)
    institution._field_cache["level"] = "Middle School"

    with pytest.raises(RuntimeError, match="program dataset failed"):
        _ = institution.programs
    assert "programs" not in institution.field_cache

    programs = institution.programs
    assert institution.programs is programs
    assert programs == ["Reading"]
    assert events == [("middle_school", Path(institution_models.educational_institution.__file__))] * 2


def test_program_loader_failure_retries_without_caching(monkeypatch: pytest.MonkeyPatch) -> None:
    from datamimic_ce.domains.shared.datasets import loader

    calls = 0

    def load_programs(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("program CSV unavailable")
        return ["Reading", "Writing", "Math"], [1.0, 1.0, 1.0]

    monkeypatch.setattr(loader, "load_weighted_values_try_dataset", load_programs)
    generator = EducationalInstitutionGenerator(dataset="US", rng=Random(4))
    institution = EducationalInstitution(generator)
    institution._field_cache["level"] = "Elementary"

    with pytest.raises(OSError, match="program CSV unavailable"):
        _ = institution.programs
    assert "programs" not in institution.field_cache

    assert institution.programs == ["Math", "Reading", "Writing"]
    assert calls == 2


def test_program_sampling_failure_retries_without_caching(monkeypatch: pytest.MonkeyPatch) -> None:
    from datamimic_ce.domains.shared.datasets import loader

    monkeypatch.setattr(
        loader,
        "load_weighted_values_try_dataset",
        lambda *args, **kwargs: (["A", "B", "C", "D"], [1.0, 1.0, 1.0, 1.0]),
    )
    failures = 1

    def sample(rng: Random, values: list[str], weights: list[float], count: int) -> list[str]:  # noqa: ARG001
        nonlocal failures
        if failures:
            failures -= 1
            raise RuntimeError("program sampling failed")
        return values[:count]

    monkeypatch.setattr(loader, "sample_weighted_no_replacement", sample)
    generator = EducationalInstitutionGenerator(dataset="US", rng=Random(5))
    institution = EducationalInstitution(generator)
    institution._field_cache["level"] = "Elementary"

    with pytest.raises(RuntimeError, match="program sampling failed"):
        _ = institution.programs
    assert "programs" not in institution.field_cache

    programs = institution.programs
    assert institution.programs is programs
    assert programs == sorted(programs)
    assert len(programs) == 3


def test_seeded_programs_first_and_level_first_keep_outputs_and_rng_state() -> None:
    programs_first, _, programs_first_rng = _institution(144)
    assert _fingerprint(programs_first_rng) == (
        "87cfc7f9c52def3dc6fd669b7b2e6bd400aaaf567ebaad719f36fbe6a03888b6"
    )
    assert programs_first.programs == [
        "Arts and Music",
        "Early Childhood Education",
        "Elementary Education",
        "Gifted and Talented Program",
        "Math Fundamentals",
        "Physical Education",
        "Reading and Literacy",
        "Science Discovery",
        "Special Education",
    ]
    assert programs_first.level == "Elementary"
    assert _fingerprint(programs_first_rng) == (
        "e9bd27fe73b7208e7f4749036caea0f8263b69f0cdabaeed0d413d04d2654e40"
    )

    level_first, _, level_first_rng = _institution(144)
    assert level_first.level == "Elementary"
    assert level_first.programs == programs_first.programs
    assert _fingerprint(level_first_rng) == (
        "e9bd27fe73b7208e7f4749036caea0f8263b69f0cdabaeed0d413d04d2654e40"
    )
