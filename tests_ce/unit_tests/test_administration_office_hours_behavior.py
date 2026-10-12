from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def _hours_data(weekdays: list[str] | None = None) -> tuple:
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] if weekdays is None else weekdays
    return (
        days,
        [1] * len(days),
        ["09:00"],
        [1],
        ["17:00"],
        [1],
        ["19:00"],
        [1],
        ["10:00"],
        [1],
        ["14:00"],
        [1],
    )


class _ScriptedRandom(Random):
    def __init__(
        self,
        *,
        choice_results: list[str] | None = None,
        choices_results: list[str] | None = None,
        random_results: list[float] | None = None,
        events: list[object] | None = None,
        fail_choices_at: int | None = None,
    ) -> None:
        super().__init__(1)
        self.choice_results = list(choice_results or [])
        self.choices_results = list(choices_results or [])
        self.random_results = list(random_results or [])
        self.events = events if events is not None else []
        self.fail_choices_at = fail_choices_at
        self.choices_calls = 0

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        self.choices_calls += 1
        self.events.append(("choices", tuple(population), tuple(weights) if weights is not None else None, k))
        if self.fail_choices_at == self.choices_calls:
            raise RuntimeError("scripted hours choices failure")
        return [self.choices_results.pop(0)]

    def getrandbits(self, k: int) -> int:
        return super().getrandbits(k)

    def random(self) -> float:
        if not self.random_results:
            return super().random()
        self.events.append("random")
        return self.random_results.pop(0)

    def choice(self, sequence):
        self.events.append(("choice", tuple(sequence)))
        return self.choice_results.pop(0)


class _ObservedGenerator(AdministrationOfficeGenerator):
    def __init__(self, *args, hours_data: tuple | None = None, events: list[object] | None = None, **kwargs) -> None:
        self.events = events if events is not None else []
        self._hours_data = _hours_data() if hours_data is None else hours_data
        super().__init__(*args, **kwargs)

    @property
    def rng(self) -> Random:
        self.events.append("rng")
        return self._rng

    def load_hours_datasets(self) -> tuple:
        self.events.append("load_hours_datasets")
        return self._hours_data


def _scripted_office(
    *,
    choices_results: list[str],
    random_results: list[float],
    choice_results: list[str] | None = None,
    weekdays: list[str] | None = None,
    events: list[object] | None = None,
    fail_choices_at: int | None = None,
) -> tuple[AdministrationOffice, _ObservedGenerator, _ScriptedRandom]:
    log = events if events is not None else []
    scripted_random_results = list(random_results)
    rng = _ScriptedRandom(
        choice_results=choice_results,
        choices_results=choices_results,
        random_results=[],
        events=log,
        fail_choices_at=fail_choices_at,
    )
    generator = _ObservedGenerator(
        dataset="US",
        rng=rng,
        events=log,
        hours_data=_hours_data(weekdays),
    )
    rng.random_results = scripted_random_results
    log.clear()
    return AdministrationOffice(generator), generator, rng


def test_seeded_hours_load_real_datasets_and_keep_rng_fingerprint() -> None:
    rng = Random(79)
    generator = AdministrationOfficeGenerator(dataset="US", rng=rng)
    office = AdministrationOffice(generator)

    assert _rng_fingerprint(rng) == "fc742aadeae5ef3b17cb4ef461268b0e290444d567d88a6dcdda1528389d93cb"
    assert office.hours_of_operation == {
        "Monday": "8:30 AM - 4:30 PM",
        "Tuesday": "8:30 AM - 4:30 PM",
        "Wednesday": "8:30 AM - 4:30 PM",
        "Thursday": "8:30 AM - 4:30 PM",
        "Friday": "8:30 AM - 4:30 PM",
        "Saturday": "Closed",
        "Sunday": "Closed",
    }
    assert _rng_fingerprint(rng) == "51c124aa43d5892b70bc38d427ba7c7cc42d35dd1b35b29e48301f05595a156f"
    assert generator.last_hours_signature == tuple(sorted(office.hours_of_operation.items()))


def test_standard_hours_draw_order_and_cached_identity() -> None:
    office, _, rng = _scripted_office(choices_results=["09:00", "17:00"], random_results=[0.8, 0.8])

    hours = office.hours_of_operation

    assert hours == {
        "Monday": "09:00 - 17:00",
        "Tuesday": "09:00 - 17:00",
        "Wednesday": "09:00 - 17:00",
        "Thursday": "09:00 - 17:00",
        "Friday": "09:00 - 17:00",
        "Saturday": "Closed",
        "Sunday": "Closed",
    }
    assert office.hours_of_operation is hours
    assert rng.events == [
        "load_hours_datasets",
        "rng",
        ("choices", ("09:00",), (1,), 1),
        ("choices", ("17:00",), (1,), 1),
        "random",
        "random",
    ]


def test_extended_weekday_and_saturday_branches_preserve_draw_order() -> None:
    office, _, rng = _scripted_office(
        choices_results=["09:00", "17:00", "Tuesday", "19:00", "10:00", "14:00"],
        random_results=[0.1, 0.1],
    )

    assert office.hours_of_operation == {
        "Monday": "09:00 - 17:00",
        "Tuesday": "09:00 - 19:00",
        "Wednesday": "09:00 - 17:00",
        "Thursday": "09:00 - 17:00",
        "Friday": "09:00 - 17:00",
        "Saturday": "10:00 - 14:00",
        "Sunday": "Closed",
    }
    assert [event for event in rng.events if event == "random"] == ["random", "random"]
    assert [event[0] for event in rng.events if isinstance(event, tuple) and event[0] == "choices"] == [
        "choices",
        "choices",
        "choices",
        "choices",
        "choices",
        "choices",
    ]


def test_repeat_signature_adjusts_one_open_day_and_updates_signature() -> None:
    baseline = {
        "Monday": "09:00 - 17:00",
        "Tuesday": "09:00 - 17:00",
        "Wednesday": "09:00 - 17:00",
        "Thursday": "09:00 - 17:00",
        "Friday": "09:00 - 17:00",
        "Saturday": "Closed",
        "Sunday": "Closed",
    }
    office, generator, rng = _scripted_office(
        choices_results=["09:00", "17:00", "19:00"],
        random_results=[0.8, 0.8],
        choice_results=["Monday"],
    )
    generator.last_hours_signature = tuple(sorted(baseline.items()))

    hours = office.hours_of_operation

    assert hours["Monday"] == "09:00 - 19:00"
    assert hours["Tuesday"] == baseline["Tuesday"]
    assert generator.last_hours_signature == tuple(sorted(hours.items()))
    assert rng.events[-2:] == [
        ("choice", ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")),
        ("choices", ("19:00",), (1,), 1),
    ]


def test_repeat_signature_with_no_open_days_uses_saturday_fallback() -> None:
    office, generator, rng = _scripted_office(
        weekdays=[],
        choices_results=["09:00", "17:00", "10:00", "14:00"],
        random_results=[0.8, 0.8],
    )
    generator.last_hours_signature = (("Saturday", "Closed"), ("Sunday", "Closed"))

    assert office.hours_of_operation == {"Saturday": "10:00 - 14:00", "Sunday": "Closed"}
    assert rng.events[-2:] == [("choices", ("10:00",), (1,), 1), ("choices", ("14:00",), (1,), 1)]


def test_hours_failure_retries_without_cache_or_signature_mutation() -> None:
    office, generator, rng = _scripted_office(
        choices_results=["09:00", "09:00", "17:00"],
        random_results=[0.8, 0.8],
        fail_choices_at=2,
    )

    with pytest.raises(RuntimeError, match="scripted hours choices failure"):
        _ = office.hours_of_operation
    assert "hours_of_operation" not in office.field_cache
    assert generator.last_hours_signature is None

    assert office.hours_of_operation["Monday"] == "09:00 - 17:00"
    assert "hours_of_operation" in office.field_cache
    assert generator.last_hours_signature == tuple(sorted(office.hours_of_operation.items()))
    assert [event for event in rng.events if event == "load_hours_datasets"] == [
        "load_hours_datasets",
        "load_hours_datasets",
    ]


def test_offices_sharing_generator_have_independent_cached_hours() -> None:
    first, generator, _ = _scripted_office(
        choices_results=["09:00", "17:00", "09:00", "17:00", "19:00"],
        random_results=[0.8, 0.8, 0.8, 0.8],
        choice_results=["Monday"],
    )
    second = AdministrationOffice(generator)
    first_hours = first.hours_of_operation
    second_hours = second.hours_of_operation

    assert first_hours is first.hours_of_operation
    assert second_hours is second.hours_of_operation
    assert first_hours is not second_hours
    assert first_hours["Monday"] == "09:00 - 17:00"
    assert second_hours["Monday"] == "09:00 - 19:00"


def test_hours_generation_delegates_to_generator() -> None:
    expected = {"Monday": "custom"}

    class CandidateGenerator(AdministrationOfficeGenerator):
        calls = 0

        def generate_hours_of_operation(self) -> dict[str, str]:
            self.calls += 1
            return expected

    generator = CandidateGenerator(dataset="US", rng=Random(79))
    office = AdministrationOffice(generator)

    assert office.hours_of_operation == expected
    assert office.hours_of_operation is expected
    assert generator.calls == 1
