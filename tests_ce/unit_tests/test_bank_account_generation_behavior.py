from datetime import datetime, timezone
from hashlib import sha256
from random import Random

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
