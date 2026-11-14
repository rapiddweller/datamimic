import re
from datetime import datetime, timezone
from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.finance.generators.bank_account_generator import BankAccountGenerator
from datamimic_ce.domains.finance.models.bank_account import BankAccount

_REFERENCE_NOW = datetime(2026, 9, 29, 10, 30, tzinfo=timezone.utc)


def _account() -> tuple[BankAccount, Random]:
    rng = Random(31)
    generator = BankAccountGenerator(dataset="DE", rng=rng, reference_now=_REFERENCE_NOW)
    return BankAccount(generator), rng


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


def test_seeded_balance_is_lazy_cached_and_preserves_full_rng_state() -> None:
    account, rng = _account()

    assert _rng_fingerprint(rng) == "6f65141f0fc70077c65866b5807ba473923846fdbc594a2d402644669479b265"
    assert account.balance == 683864.273453267
    state_after_read = rng.getstate()
    assert _rng_fingerprint(rng) == "4f6384d0c825860f060ff2205d8b65e1d8561313556313f69ad744576196a5b1"

    assert account.balance == 683864.273453267
    assert rng.getstate() == state_after_read


def test_setting_balance_before_first_read_avoids_random_draw() -> None:
    account, rng = _account()
    state_before_set = rng.getstate()

    account.balance = 123.45

    assert account.balance == 123.45
    assert rng.getstate() == state_before_set
    assert _rng_fingerprint(rng) == "6f65141f0fc70077c65866b5807ba473923846fdbc594a2d402644669479b265"


def test_setting_balance_after_first_read_overrides_cached_value_without_draw() -> None:
    account, rng = _account()
    assert account.balance == 683864.273453267
    state_after_read = rng.getstate()

    account.balance = 987.65

    assert account.balance == 987.65
    assert rng.getstate() == state_after_read
    assert _rng_fingerprint(rng) == "4f6384d0c825860f060ff2205d8b65e1d8561313556313f69ad744576196a5b1"


def _iban_is_valid(iban: str) -> bool:
    moved = iban[4:] + iban[:4]
    return int("".join(str(int(c, 36)) for c in moved)) % 97 == 1


# Independent of the generator: lengths from the ISO 13616 registry, structure as one regular expression.
_IBAN_SHAPES = {
    "AT": (20, r"AT\d{18}"),
    "CH": (21, r"CH\d{7}[0-9A-Z]{12}"),
    "DE": (22, r"DE\d{20}"),
    "FR": (27, r"FR\d{12}[0-9A-Z]{11}\d{2}"),
    "GB": (22, r"GB\d{2}[A-Z]{4}\d{14}"),
    "IT": (27, r"IT\d{2}[A-Z]\d{10}[0-9A-Z]{12}"),
    "NL": (18, r"NL\d{2}[A-Z]{4}\d{10}"),
    "PT": (25, r"PT\d{23}"),
}


@pytest.mark.parametrize("country", sorted(_IBAN_SHAPES))
def test_iban_has_the_length_structure_and_check_digits_of_its_country(country: str) -> None:
    length, shape = _IBAN_SHAPES[country]
    rng = Random(5)
    for _ in range(300):
        account = BankAccount(BankAccountGenerator(dataset=country, rng=rng, reference_now=_REFERENCE_NOW))
        iban = account.iban
        assert iban is not None
        assert len(iban) == length
        assert re.fullmatch(shape, iban), iban
        assert _iban_is_valid(iban)


@pytest.mark.parametrize("country", ["US", "VN", "BE", "ES"])
def test_country_without_an_iban_scheme_has_no_iban(country: str) -> None:
    account = BankAccount(BankAccountGenerator(dataset=country, rng=Random(5), reference_now=_REFERENCE_NOW))
    assert account.iban is None
