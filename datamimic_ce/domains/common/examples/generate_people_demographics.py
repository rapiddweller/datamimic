"""
Examples: Person generation with DemographicConfig and seeded RNG.

WHY: Demonstrate deterministic runs and demographic constraints (age bounds)
without changing any model behavior. All randomness flows through injected RNGs
and all dataset I/O is handled in generators.
"""

from __future__ import annotations

from random import Random

from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.domains.common.services.person_service import PersonService


def generate_seeded_people(count: int = 3) -> None:
    #  A fixed seed yields reproducible sequences across runs
    svc = PersonService(dataset="US", rng=Random(1234))
    for p in svc.generate_batch(count):
        print(p.to_dict())


def generate_people_age_range(min_age: int = 30, max_age: int = 40, count: int = 3) -> None:
    #  Apply demographic constraints via DemographicConfig
    cfg = DemographicConfig(age_min=min_age, age_max=max_age)
    svc = PersonService(dataset="US", demographic_config=cfg, rng=Random(77))
    for p in svc.generate_batch(count):
        print({"name": p.name, "age": p.age, "gender": p.gender})


if __name__ == "__main__":
    print("-- Seeded People --")
    generate_seeded_people()
    print("-- People with age range 30-40 --")
    generate_people_age_range()
