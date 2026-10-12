from hashlib import sha256
from random import Random

import pytest

from datamimic_ce.domains.finance.generators.credit_card_generator import CreditCardGenerator
from datamimic_ce.domains.finance.models.credit_card import CreditCard


def _card(seed: int) -> tuple[CreditCard, CreditCardGenerator, Random]:
    rng = Random(seed)
    generator = CreditCardGenerator(dataset="US", rng=rng)
    return CreditCard(generator), generator, rng


def _rng_fingerprint(rng: Random) -> str:
    return sha256(repr(rng.getstate()).encode()).hexdigest()


@pytest.mark.parametrize(
    ("seed", "expected"),
    [
        (
            731,
            {
                "card_number": "5948844160734575",
                "cvv": "648",
                "cvc_number": "914",
            },
        ),
        (
            42,
            {
                "card_number": "349600133890837",
                "cvv": "8637",
                "cvc_number": "9402",
            },
        ),
    ],
)
def test_seeded_card_credentials_and_full_rng_state_are_stable(seed, expected):
    card, _, rng = _card(seed)

    actual = {name: getattr(card, name) for name in ("card_number", "cvv", "cvc_number")}
    state_after_first_reads = rng.getstate()

    assert actual == expected
    assert actual["cvv"] != actual["cvc_number"]
    assert {name: getattr(card, name) for name in expected} == expected
    assert rng.getstate() == state_after_first_reads
    assert _rng_fingerprint(rng) == (
        "852708e796dff62755e070788f140e9efe0768a57657d1d420dd73c2c7ccd82d"
        if seed == 731
        else "d4d958e09fc1d64a9930c4447d044b5f24f9e0c76584210f16cae114d3c0c53e"
    )


@pytest.mark.parametrize(
    ("order", "expected"),
    [
        (
            ("card_number", "cvv", "cvc_number"),
            {"card_number": "5948844160734575", "cvv": "648", "cvc_number": "914"},
        ),
        (
            ("cvc_number", "cvv", "card_number"),
            {"cvc_number": "948", "cvv": "844", "card_number": "5160734576489149"},
        ),
        (
            ("cvv", "card_number", "cvc_number"),
            {"cvv": "948", "card_number": "5844160734576482", "cvc_number": "914"},
        ),
    ],
)
def test_card_credential_access_order_keeps_outputs_and_complete_rng_state(order, expected):
    card, _, rng = _card(731)

    assert {name: getattr(card, name) for name in order} == expected
    assert _rng_fingerprint(rng) == "852708e796dff62755e070788f140e9efe0768a57657d1d420dd73c2c7ccd82d"


def test_cvv_keeps_leading_zeroes():
    card, _, rng = _card(20)

    assert card.cvv == "066"
    assert _rng_fingerprint(rng) == "b3f2c5d211b6ca334445ce2631c24da6e5ee968052955626b984aa7a35ba2104"


@pytest.mark.parametrize("length", [3, 4])
def test_card_number_returns_prefix_when_prefix_fills_or_exceeds_length(monkeypatch, length):
    card, generator, rng = _card(731)
    monkeypatch.setattr(
        generator,
        "get_card_specs",
        lambda: {"type": "TEST", "prefix": "4012", "length": length, "cvv_length": 0},
    )
    state_before = rng.getstate()

    assert card.card_number == "4012"
    assert card.cvv == ""
    assert card.cvc_number == ""
    assert rng.getstate() == state_before


@pytest.mark.parametrize(
    ("order", "expected", "rng_state"),
    [
        (
            ("is_active", "credit_limit", "current_balance"),
            {"is_active": False, "credit_limit": 101629.98014370656, "current_balance": 760699.2167596506},
            "456260d07473761a4ffa5149d7b5e34be611474cc5508a7c3a82bc1b49483565",
        ),
        (
            ("current_balance", "credit_limit", "is_active"),
            {"current_balance": 442797.5197431716, "credit_limit": 684433.414601703, "is_active": False},
            "613d418f125a9942c86af2609ebf228193c849ae747f6c42fd44ab407b53e824",
        ),
    ],
)
def test_seeded_card_status_and_amounts_keep_access_order_and_rng_state(order, expected, rng_state):
    card, _, rng = _card(731)

    actual = {name: getattr(card, name) for name in order}
    assert actual == expected
    state_after_reads = rng.getstate()

    assert {name: getattr(card, name) for name in order} == expected
    assert rng.getstate() == state_after_reads
    assert _rng_fingerprint(rng) == rng_state


def test_shared_generator_keeps_separate_model_property_caches():
    rng = Random(2026)
    generator = CreditCardGenerator(dataset="US", rng=rng)
    first = CreditCard(generator)
    second = CreditCard(generator)

    first_limit = first.credit_limit
    second_limit = second.credit_limit
    state_after_both = rng.getstate()

    assert first_limit == 751274.1811745012
    assert second_limit == 586933.7391269092
    assert first.credit_limit == first_limit
    assert second.credit_limit == second_limit
    assert rng.getstate() == state_after_both
    assert _rng_fingerprint(rng) == "b38a8e0e30c7307e20bdc1089d15ef617554b07adfe771cf10b5742ef39d6e6f"


def test_current_balance_is_not_limited_by_credit_limit():
    card, _, rng = _card(1)

    assert card.credit_limit == 651940.7281570674
    assert card.current_balance == 788743.6900770485
    assert card.current_balance > card.credit_limit
    assert _rng_fingerprint(rng) == "e3abf7fcf6c5cfed49d3d2b6b5fb66e8a6001e75b464754e0865e25f64204dcf"


def test_credit_card_to_dict_keeps_public_key_order():
    card, _, _ = _card(42)

    assert tuple(card.to_dict()) == (
        "card_type",
        "card_number",
        "card_provider",
        "card_holder",
        "expiration_date",
        "cvv",
        "cvc_number",
        "is_active",
        "credit_limit",
        "current_balance",
        "issue_date",
        "bank_name",
        "bank_code",
        "bic",
        "bin",
        "iban",
    )
