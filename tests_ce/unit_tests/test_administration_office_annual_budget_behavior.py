from __future__ import annotations

from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.public_sector.generators.administration_office_generator import AdministrationOfficeGenerator
from datamimic_ce.domains.public_sector.models.administration_office import AdministrationOffice


def _fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


class _BudgetRandom(Random):
    def __init__(self, values: list[float | Exception], events: list[object]) -> None:
        super().__init__(13)
        self.values = values
        self.events = events

    def uniform(self, a: float, b: float) -> float:
        self.events.append(("uniform", a, b))
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


class _ObservedOfficeGenerator(AdministrationOfficeGenerator):
    def __init__(self, rng: Random, events: list[object]) -> None:
        self.events = events
        self.rng_reads = 0
        super().__init__(dataset="US", rng=rng)

    @property
    def rng(self) -> Random:
        self.rng_reads += 1
        self.events.append("rng")
        return self._rng


class _InputOffice(AdministrationOffice):
    def __init__(
        self,
        generator: AdministrationOfficeGenerator,
        events: list[object],
        office_type: str,
        staff_count: int,
        *,
        fail_input: str | None = None,
    ) -> None:
        super().__init__(generator)
        self.events = events
        self.office_type = office_type
        self._staff_count = staff_count
        self.fail_input = fail_input

    @property
    def type(self) -> str:
        self.events.append("type")
        if self.fail_input == "type":
            raise RuntimeError("scripted type failure")
        return self.office_type

    @property
    def staff_count(self) -> int:
        self.events.append("staff_count")
        if self.fail_input == "staff_count":
            raise RuntimeError("scripted staff failure")
        return self._staff_count


@pytest.mark.parametrize(
    ("office_type", "multiplier_bounds", "multiplier"),
    [
        ("Federal State County", (1.5, 3.0), 1.5),
        ("State County", (1.2, 2.0), 1.2),
        ("County", (1.0, 1.5), 1.0),
        ("Municipal", (0.8, 1.2), 0.8),
        ("Unclassified", (0.8, 1.2), 0.8),
    ],
)
def test_annual_budget_preserves_type_precedence_bounds_draw_order_and_formula(
    office_type: str,
    multiplier_bounds: tuple[float, float],
    multiplier: float,
) -> None:
    events: list[object] = []
    rng = _BudgetRandom([100000.0, multiplier, 1.0], events)
    generator = _ObservedOfficeGenerator(rng, events)
    office = _InputOffice(generator, events, office_type, 2)

    assert office.annual_budget == round(2 * 100000.0 * multiplier * 1.0 / 1000) * 1000
    assert events == [
        "type",
        "staff_count",
        "rng",
        ("uniform", 80000, 120000),
        ("uniform", *multiplier_bounds),
        ("uniform", 0.9, 1.1),
    ]
    assert generator.rng_reads == 1


def test_annual_budget_rounds_to_nearest_thousand_and_zero_staff_still_draws() -> None:
    events: list[object] = []
    rng = _BudgetRandom([100600.0, 2.5, 1.0, 80000.0, 1.5, 0.9], events)
    generator = _ObservedOfficeGenerator(rng, events)
    half_thousand = _InputOffice(generator, events, "Federal", 1)
    zero_staff = _InputOffice(generator, events, "Federal", 0)

    assert half_thousand.annual_budget == 252000
    assert zero_staff.annual_budget == 0
    assert events.count(("uniform", 80000, 120000)) == 2
    assert events.count(("uniform", 1.5, 3.0)) == 2
    assert events.count(("uniform", 0.9, 1.1)) == 2
    assert generator.rng_reads == 2


def test_annual_budget_third_draw_failure_retries_all_draws_without_rng_rollback() -> None:
    class FailOnThirdUniform(Random):
        def __init__(self) -> None:
            super().__init__(13)
            self.uniform_calls: list[tuple[float, float, float]] = []

        def uniform(self, a: float, b: float) -> float:
            value = super().uniform(a, b)
            self.uniform_calls.append((a, b, value))
            if len(self.uniform_calls) == 3:
                raise RuntimeError("scripted third budget draw failure")
            return value

    events: list[object] = []
    rng = FailOnThirdUniform()
    generator = _ObservedOfficeGenerator(rng, events)
    office = AdministrationOffice(generator)
    office._field_cache.update(type="Federal", staff_count=2)
    initial_state = rng.getstate()

    with pytest.raises(RuntimeError, match="scripted third budget draw failure"):
        _ = office.annual_budget
    assert "annual_budget" not in office.field_cache
    assert rng.getstate() != initial_state
    assert [(a, b) for a, b, _ in rng.uniform_calls] == [
        (80000, 120000),
        (1.5, 3.0),
        (0.9, 1.1),
    ]
    state_after_failure = rng.getstate()

    budget = office.annual_budget
    retry_draws = rng.uniform_calls[3:]
    expected = round(2 * retry_draws[0][2] * retry_draws[1][2] * retry_draws[2][2] / 1000) * 1000
    assert budget == expected
    assert rng.getstate() != state_after_failure
    assert [(a, b) for a, b, _ in retry_draws] == [
        (80000, 120000),
        (1.5, 3.0),
        (0.9, 1.1),
    ]
    assert len(rng.uniform_calls) == 6
    assert generator.rng_reads == 2


@pytest.mark.parametrize("failure", ["type", "staff_count"])
def test_annual_budget_input_failure_precedes_rng(failure: str) -> None:
    events: list[object] = []
    generator = _ObservedOfficeGenerator(_BudgetRandom([100000.0, 1.5, 1.0], events), events)
    office = _InputOffice(generator, events, "Federal", 2, fail_input=failure)

    with pytest.raises(RuntimeError, match="scripted (type|staff) failure"):
        _ = office.annual_budget
    assert "annual_budget" not in office.field_cache
    assert events == (["type"] if failure == "type" else ["type", "staff_count"])
    assert generator.rng_reads == 0


def test_annual_budget_draw_failure_is_uncached_and_retry_draws_again() -> None:
    events: list[object] = []
    rng = _BudgetRandom([RuntimeError("scripted budget draw failure"), 100000.0, 1.5, 1.0], events)
    generator = _ObservedOfficeGenerator(rng, events)
    office = AdministrationOffice(generator)
    office._field_cache.update(type="Federal", staff_count=2)

    with pytest.raises(RuntimeError, match="scripted budget draw failure"):
        _ = office.annual_budget
    assert "annual_budget" not in office.field_cache
    assert generator.rng_reads == 1

    assert office.annual_budget == 300000
    state = rng.getstate()
    assert office.annual_budget == 300000
    assert rng.getstate() == state
    assert generator.rng_reads == 2
    assert events == [
        "rng",
        ("uniform", 80000, 120000),
        "rng",
        ("uniform", 80000, 120000),
        ("uniform", 1.5, 3.0),
        ("uniform", 0.9, 1.1),
    ]


def test_annual_budget_delegates_with_type_then_staff_count() -> None:
    events: list[object] = []

    class CandidateGenerator(_ObservedOfficeGenerator):
        def generate_annual_budget(self, office_type: str, staff_count: int) -> int:
            events.append(("generate_annual_budget", office_type, staff_count))
            return 123000

    generator = CandidateGenerator(_BudgetRandom([], events), events)
    office = _InputOffice(generator, events, "Federal Office", 12)

    assert office.annual_budget == 123000
    assert events == ["type", "staff_count", ("generate_annual_budget", "Federal Office", 12)]
    assert generator.rng_reads == 0


def test_annual_budget_access_order_and_successive_offices_preserve_seeded_outputs_and_states() -> None:
    budget_first_rng = Random(701)
    budget_first_generator = AdministrationOfficeGenerator(dataset="US", rng=budget_first_rng)
    first = AdministrationOffice(budget_first_generator)
    assert _fingerprint(budget_first_rng) == "5bfc9860f39a4f496cbc2cc7571ec69957881959c9bb617b6e6ef7f97cfa2a48"
    assert first.annual_budget == 881000
    assert first.type == "Department of Motor Vehicles"
    assert first.staff_count == 10
    assert _fingerprint(budget_first_rng) == "d3dd46496e079b275cb3c4d90bb90887388a608381f61e9ee5ad2e02745104ea"

    second = AdministrationOffice(budget_first_generator)
    assert second.annual_budget == 3972000
    assert second.type == "Social Services Office"
    assert second.staff_count == 46
    assert _fingerprint(budget_first_rng) == "bf7c6cd4df627bc772f96be269ef0c491b2dda726ef7014d83d84b2ef791b314"

    fields_first_rng = Random(701)
    fields_first_generator = AdministrationOfficeGenerator(dataset="US", rng=fields_first_rng)
    fields_first = AdministrationOffice(fields_first_generator)
    assert fields_first.type == "Department of Motor Vehicles"
    assert fields_first.staff_count == 10
    assert _fingerprint(fields_first_rng) == "18720a551ca508309d144c06959254a72058cfa0b411b89208308908e1df53b9"
    assert fields_first.annual_budget == 881000
    assert _fingerprint(fields_first_rng) == "d3dd46496e079b275cb3c4d90bb90887388a608381f61e9ee5ad2e02745104ea"
