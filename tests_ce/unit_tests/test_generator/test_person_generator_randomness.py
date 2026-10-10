# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.

from __future__ import annotations

from random import Random

from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount
from datamimic_ce.domains.shared.generators.person_generator import PersonGenerator
from datamimic_ce.domains.shared.models.person import Person
from datamimic_ce.randomness import cumulated_index


def test_person_generator_without_seed_produces_varied_people() -> None:
    generator = PersonGenerator()
    cohort = [Person(generator) for _ in range(10)]
    # Combine discriminating fields so any deterministic regression is caught despite random collisions being unlikely.
    signatures = {(person.name, person.email, person.age) for person in cohort}

    assert len(signatures) > 1, "Expected unseeded PersonGenerator to emit varied people"


def test_bank_account_generator_without_seed_produces_varied_accounts() -> None:
    generator = BankAccountGenerator()
    accounts = [BankAccount(generator) for _ in range(10)]
    # Account numbers derive from RNG-backed Faker, so uniqueness guards against silent seeding to a constant.
    account_numbers = {account.account_number for account in accounts}

    assert len(account_numbers) > 1, "Expected unseeded BankAccountGenerator to emit varied account numbers"


def test_person_nobility_title_is_string_for_other_gender() -> None:
    generator = PersonGenerator(
        female_quota=0.0,
        other_gender_quota=1.0,
        noble_quota=1.0,
        rng=Random(42),
    )
    person = Person(generator)

    assert isinstance(person.nobility_title, str)


def test_cumulated_sampling_keeps_five_draw_order_for_a_seeded_rng() -> None:
    rng = Random(23)
    reference = Random(23)

    assert [cumulated_index(rng, 10) for _ in range(5)] == [4, 5, 3, 4, 6]
    for _ in range(25):
        reference.randint(0, 10)
    assert rng.getstate() == reference.getstate()
